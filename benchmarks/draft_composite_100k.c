#include <openssl/core_names.h>
#include <openssl/evp.h>
#include <openssl/params.h>
#include <openssl/sha.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static const unsigned char prefix[] = "CompositeAlgorithmSignatures2025";

typedef struct {
    const char *name;
    const char *mldsa;
    const char *group;
    const EVP_MD *(*ph)(void);
    const EVP_MD *(*ecdsa_md)(void);
    const char *label;
    size_t mldsa_sig_len;
} variant;

static const variant variants[] = {
    {"ML-DSA-44 + ECDSA P-256", "ML-DSA-44", "prime256v1", EVP_sha256,
     EVP_sha256, "COMPSIG-MLDSA44-ECDSA-P256-SHA256", 2420},
    {"ML-DSA-65 + ECDSA P-256", "ML-DSA-65", "prime256v1", EVP_sha512,
     EVP_sha256, "COMPSIG-MLDSA65-ECDSA-P256-SHA512", 3309},
    {"ML-DSA-87 + ECDSA P-384", "ML-DSA-87", "secp384r1", EVP_sha512,
     EVP_sha384, "COMPSIG-MLDSA87-ECDSA-P384-SHA512", 4627},
};

static void fail(const char *what) {
    fprintf(stderr, "error: %s\n", what);
    exit(1);
}

static double now_seconds(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) fail("clock_gettime");
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static EVP_PKEY *generate_key(const char *algorithm, const char *group) {
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new_from_name(NULL, algorithm, NULL);
    EVP_PKEY *key = NULL;
    if (!ctx || EVP_PKEY_keygen_init(ctx) <= 0) fail("keygen init");
    if (group) {
        OSSL_PARAM params[] = {
            OSSL_PARAM_construct_utf8_string(OSSL_PKEY_PARAM_GROUP_NAME,
                                             (char *)group, 0),
            OSSL_PARAM_construct_end()
        };
        if (EVP_PKEY_CTX_set_params(ctx, params) <= 0) fail("set EC group");
    }
    if (EVP_PKEY_generate(ctx, &key) <= 0) fail("key generation");
    EVP_PKEY_CTX_free(ctx);
    return key;
}

static size_t raw_public_key_length(EVP_PKEY *key, int mldsa) {
    size_t len = 0;
    const char *param = OSSL_PKEY_PARAM_PUB_KEY;
    if (mldsa) {
        if (!EVP_PKEY_get_raw_public_key(key, NULL, &len))
            fail("get ML-DSA public key length");
        return len;
    }
    if (!EVP_PKEY_get_octet_string_param(key, param, NULL, 0, &len))
        fail("get public key length");
    return len;
}

static size_t sign_once(EVP_PKEY *key, const EVP_MD *md,
                        const unsigned char *ctx_string, size_t ctx_len,
                        const unsigned char *msg, size_t msg_len,
                        unsigned char *sig, size_t sig_capacity) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    size_t sig_len = sig_capacity;
    OSSL_PARAM params[2] = {OSSL_PARAM_construct_end(), OSSL_PARAM_construct_end()};
    if (!ctx) fail("signature context allocation");
    if (ctx_string) {
        params[0] = OSSL_PARAM_construct_octet_string(
            OSSL_SIGNATURE_PARAM_CONTEXT_STRING, (void *)ctx_string, ctx_len);
    }
    if (EVP_DigestSignInit_ex(ctx, NULL, md ? EVP_MD_get0_name(md) : NULL,
                              NULL, NULL, key, params) <= 0 ||
        EVP_DigestSign(ctx, sig, &sig_len, msg, msg_len) <= 0)
        fail("sign");
    EVP_MD_CTX_free(ctx);
    return sig_len;
}

static int verify_once(EVP_PKEY *key, const EVP_MD *md,
                       const unsigned char *ctx_string, size_t ctx_len,
                       const unsigned char *msg, size_t msg_len,
                       const unsigned char *sig, size_t sig_len) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    OSSL_PARAM params[2] = {OSSL_PARAM_construct_end(), OSSL_PARAM_construct_end()};
    int ok;
    if (!ctx) fail("verification context allocation");
    if (ctx_string) {
        params[0] = OSSL_PARAM_construct_octet_string(
            OSSL_SIGNATURE_PARAM_CONTEXT_STRING, (void *)ctx_string, ctx_len);
    }
    if (EVP_DigestVerifyInit_ex(ctx, NULL, md ? EVP_MD_get0_name(md) : NULL,
                                NULL, NULL, key, params) <= 0)
        fail("verify init");
    ok = EVP_DigestVerify(ctx, sig, sig_len, msg, msg_len);
    EVP_MD_CTX_free(ctx);
    return ok == 1;
}

static size_t make_representative(const variant *v, const unsigned char *msg,
                                  size_t msg_len, unsigned char *out) {
    unsigned int hash_len = 0;
    unsigned char hash[EVP_MAX_MD_SIZE];
    EVP_MD_CTX *hash_ctx = EVP_MD_CTX_new();
    size_t offset = 0, label_len = strlen(v->label);
    if (!hash_ctx || EVP_DigestInit_ex(hash_ctx, v->ph(), NULL) <= 0 ||
        EVP_DigestUpdate(hash_ctx, msg, msg_len) <= 0 ||
        EVP_DigestFinal_ex(hash_ctx, hash, &hash_len) <= 0)
        fail("pre-hash");
    EVP_MD_CTX_free(hash_ctx);
    memcpy(out + offset, prefix, sizeof(prefix) - 1); offset += sizeof(prefix) - 1;
    memcpy(out + offset, v->label, label_len); offset += label_len;
    out[offset++] = 0; /* application ctx is empty for this benchmark */
    memcpy(out + offset, hash, hash_len); offset += hash_len;
    return offset;
}

int main(int argc, char **argv) {
    uint64_t iterations = argc > 1 ? strtoull(argv[1], NULL, 10) : 100000;
    const unsigned char message[32] = {0};
    unsigned char representative[256];
    unsigned char mldsa_sig[5000], ecdsa_sig[256];
    if (!iterations) fail("iterations must be positive");

    puts("variant,iterations,sign_seconds,verify_seconds,public_key_bytes,signature_bytes_min,signature_bytes_max,signature_bytes_mean");
    for (size_t vi = 0; vi < sizeof(variants) / sizeof(variants[0]); vi++) {
        const variant *v = &variants[vi];
        EVP_PKEY *mldsa = generate_key(v->mldsa, NULL);
        EVP_PKEY *ecdsa = generate_key("EC", v->group);
        size_t rep_len = make_representative(v, message, sizeof(message), representative);
        size_t label_len = strlen(v->label), sig_min = SIZE_MAX, sig_max = 0;
        uint64_t sig_total = 0;
        double start, sign_seconds, verify_seconds;

        size_t ml_len = sign_once(mldsa, NULL, (const unsigned char *)v->label,
                                  label_len, representative, rep_len,
                                  mldsa_sig, sizeof(mldsa_sig));
        size_t ec_len = sign_once(ecdsa, v->ecdsa_md(), NULL, 0,
                                  representative, rep_len, ecdsa_sig,
                                  sizeof(ecdsa_sig));
        if (ml_len != v->mldsa_sig_len ||
            !verify_once(mldsa, NULL, (const unsigned char *)v->label, label_len,
                         representative, rep_len, mldsa_sig, ml_len) ||
            !verify_once(ecdsa, v->ecdsa_md(), NULL, 0, representative, rep_len,
                         ecdsa_sig, ec_len))
            fail("self-test");
        mldsa_sig[0] ^= 1;
        if (verify_once(mldsa, NULL, (const unsigned char *)v->label, label_len,
                        representative, rep_len, mldsa_sig, ml_len))
            fail("negative self-test");
        mldsa_sig[0] ^= 1;

        start = now_seconds();
        for (uint64_t i = 0; i < iterations; i++) {
            ml_len = sign_once(mldsa, NULL, (const unsigned char *)v->label,
                               label_len, representative, rep_len,
                               mldsa_sig, sizeof(mldsa_sig));
            ec_len = sign_once(ecdsa, v->ecdsa_md(), NULL, 0,
                               representative, rep_len, ecdsa_sig,
                               sizeof(ecdsa_sig));
            size_t combined = ml_len + ec_len;
            if (combined < sig_min) sig_min = combined;
            if (combined > sig_max) sig_max = combined;
            sig_total += combined;
        }
        sign_seconds = now_seconds() - start;

        start = now_seconds();
        for (uint64_t i = 0; i < iterations; i++) {
            if (!verify_once(mldsa, NULL, (const unsigned char *)v->label,
                             label_len, representative, rep_len,
                             mldsa_sig, ml_len) ||
                !verify_once(ecdsa, v->ecdsa_md(), NULL, 0, representative,
                             rep_len, ecdsa_sig, ec_len))
                fail("benchmark verification");
        }
        verify_seconds = now_seconds() - start;

        printf("%s,%llu,%.6f,%.6f,%zu,%zu,%zu,%.3f\n", v->name,
               (unsigned long long)iterations, sign_seconds, verify_seconds,
               raw_public_key_length(mldsa, 1) + raw_public_key_length(ecdsa, 0),
               sig_min, sig_max, (double)sig_total / (double)iterations);
        EVP_PKEY_free(mldsa);
        EVP_PKEY_free(ecdsa);
    }
    return 0;
}
