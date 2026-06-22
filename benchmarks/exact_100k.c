#include <openssl/evp.h>
#include <openssl/rsa.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

struct algorithm {
    const char *name;
    const char *key_type;
    const char *digest;
    const char *group;
    int rsa_bits;
};

static const struct algorithm algorithms[] = {
    {"RSA-2048/SHA-256", "RSA", "SHA256", NULL, 2048},
    {"P-256/SHA-256", "EC", "SHA256", "P-256", 0},
    {"Ed25519", "ED25519", NULL, NULL, 0},
    {"ML-DSA-44", "ML-DSA-44", NULL, NULL, 0},
    {"ML-DSA-65", "ML-DSA-65", NULL, NULL, 0},
    {"ML-DSA-87", "ML-DSA-87", NULL, NULL, 0},
};

static double monotonic_seconds(void) {
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value) != 0) {
        return -1.0;
    }
    return (double)value.tv_sec + (double)value.tv_nsec / 1000000000.0;
}

static EVP_PKEY *generate_key(const struct algorithm *algorithm) {
    EVP_PKEY_CTX *context = EVP_PKEY_CTX_new_from_name(NULL, algorithm->key_type, NULL);
    EVP_PKEY *key = NULL;
    if (context == NULL || EVP_PKEY_keygen_init(context) <= 0) {
        EVP_PKEY_CTX_free(context);
        return NULL;
    }
    if (algorithm->rsa_bits && EVP_PKEY_CTX_set_rsa_keygen_bits(context, algorithm->rsa_bits) <= 0) {
        EVP_PKEY_CTX_free(context);
        return NULL;
    }
    if (algorithm->group && EVP_PKEY_CTX_set_group_name(context, algorithm->group) <= 0) {
        EVP_PKEY_CTX_free(context);
        return NULL;
    }
    if (EVP_PKEY_generate(context, &key) <= 0) {
        key = NULL;
    }
    EVP_PKEY_CTX_free(context);
    return key;
}

static int sign_once(EVP_PKEY *key, const struct algorithm *algorithm,
                     const unsigned char *message, size_t message_length,
                     unsigned char *signature, size_t *signature_length) {
    EVP_MD_CTX *context = EVP_MD_CTX_new();
    int result = 0;
    if (context != NULL &&
        EVP_DigestSignInit_ex(context, NULL, algorithm->digest, NULL, NULL, key, NULL) > 0 &&
        EVP_DigestSign(context, signature, signature_length, message, message_length) > 0) {
        result = 1;
    }
    EVP_MD_CTX_free(context);
    return result;
}

static int verify_once(EVP_PKEY *key, const struct algorithm *algorithm,
                       const unsigned char *message, size_t message_length,
                       const unsigned char *signature, size_t signature_length) {
    EVP_MD_CTX *context = EVP_MD_CTX_new();
    int result = 0;
    if (context != NULL &&
        EVP_DigestVerifyInit_ex(context, NULL, algorithm->digest, NULL, NULL, key, NULL) > 0 &&
        EVP_DigestVerify(context, signature, signature_length, message, message_length) == 1) {
        result = 1;
    }
    EVP_MD_CTX_free(context);
    return result;
}

static void benchmark(const struct algorithm *algorithm, uint64_t iterations) {
    static const unsigned char message[32] = {
        0x70, 0x71, 0x63, 0x2d, 0x72, 0x70, 0x6b, 0x69,
        0x2d, 0x6c, 0x61, 0x62, 0x2d, 0x31, 0x30, 0x30,
        0x6b, 0x2d, 0x65, 0x78, 0x61, 0x63, 0x74, 0x2d,
        0x62, 0x65, 0x6e, 0x63, 0x68, 0x2d, 0x76, 0x31
    };
    EVP_PKEY *key = NULL;
    unsigned char *signature = NULL;
    size_t signature_capacity = 0;
    size_t signature_length = 0;
    double keygen_start, keygen_seconds, sign_start, sign_seconds, verify_start, verify_seconds;
    uint64_t index;

    keygen_start = monotonic_seconds();
    key = generate_key(algorithm);
    keygen_seconds = monotonic_seconds() - keygen_start;
    if (key == NULL) {
        printf("%s,unsupported,key generation failed,,,,,\n", algorithm->name);
        fflush(stdout);
        return;
    }

    signature_capacity = (size_t)EVP_PKEY_get_size(key);
    signature = OPENSSL_malloc(signature_capacity);
    if (signature == NULL) {
        printf("%s,unsupported,signature allocation failed,,,,,\n", algorithm->name);
        EVP_PKEY_free(key);
        fflush(stdout);
        return;
    }

    signature_length = signature_capacity;
    if (!sign_once(key, algorithm, message, sizeof(message), signature, &signature_length) ||
        !verify_once(key, algorithm, message, sizeof(message), signature, signature_length)) {
        printf("%s,unsupported,EVP sign or verify failed,,,,,\n", algorithm->name);
        OPENSSL_free(signature);
        EVP_PKEY_free(key);
        fflush(stdout);
        return;
    }

    sign_start = monotonic_seconds();
    for (index = 0; index < iterations; index++) {
        signature_length = signature_capacity;
        if (!sign_once(key, algorithm, message, sizeof(message), signature, &signature_length)) {
            printf("%s,unsupported,sign failed at iteration %llu,,,,,\n",
                   algorithm->name, (unsigned long long)index);
            OPENSSL_free(signature);
            EVP_PKEY_free(key);
            fflush(stdout);
            return;
        }
    }
    sign_seconds = monotonic_seconds() - sign_start;

    verify_start = monotonic_seconds();
    for (index = 0; index < iterations; index++) {
        if (!verify_once(key, algorithm, message, sizeof(message), signature, signature_length)) {
            printf("%s,unsupported,verify failed at iteration %llu,,,,,\n",
                   algorithm->name, (unsigned long long)index);
            OPENSSL_free(signature);
            EVP_PKEY_free(key);
            fflush(stdout);
            return;
        }
    }
    verify_seconds = monotonic_seconds() - verify_start;

    printf("%s,confirmed,,%.9f,%.9f,%.9f,%zu,%llu\n",
           algorithm->name, keygen_seconds, sign_seconds, verify_seconds,
           signature_length, (unsigned long long)iterations);
    OPENSSL_free(signature);
    EVP_PKEY_free(key);
    fflush(stdout);
}

int main(int argc, char **argv) {
    uint64_t iterations = 100000;
    size_t index;
    if (argc == 2) {
        iterations = strtoull(argv[1], NULL, 10);
        if (iterations == 0) {
            fprintf(stderr, "iterations must be positive\n");
            return 2;
        }
    }
    printf("algorithm,status,reason,keygen_seconds,sign_seconds,verify_seconds,signature_bytes,iterations\n");
    fflush(stdout);
    for (index = 0; index < sizeof(algorithms) / sizeof(algorithms[0]); index++) {
        benchmark(&algorithms[index], iterations);
    }
    return 0;
}
