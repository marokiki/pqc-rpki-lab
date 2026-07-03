#include <openssl/evp.h>
#include <openssl/rsa.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/resource.h>

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

static void benchmark(const struct algorithm *algorithm, uint64_t iterations, size_t message_length) {
    unsigned char *message = NULL;
    EVP_PKEY *key = NULL;
    unsigned char *signature = NULL;
    size_t signature_capacity = 0;
    size_t signature_length = 0;
    double keygen_start, keygen_seconds, sign_start, sign_seconds, verify_start, verify_seconds;
    uint64_t index;
    struct rusage usage;

    message = OPENSSL_malloc(message_length);
    if (message == NULL) {
        printf("%s,unsupported,message allocation failed,,,,,,%zu,\n", algorithm->name, message_length);
        return;
    }
    memset(message, 0x5a, message_length);

    keygen_start = monotonic_seconds();
    key = generate_key(algorithm);
    keygen_seconds = monotonic_seconds() - keygen_start;
    if (key == NULL) {
        printf("%s,unsupported,key generation failed,,,,,,%zu,\n", algorithm->name, message_length);
        OPENSSL_free(message);
        fflush(stdout);
        return;
    }

    signature_capacity = (size_t)EVP_PKEY_get_size(key);
    signature = OPENSSL_malloc(signature_capacity);
    if (signature == NULL) {
        printf("%s,unsupported,signature allocation failed,,,,,,%zu,\n", algorithm->name, message_length);
        EVP_PKEY_free(key);
        OPENSSL_free(message);
        fflush(stdout);
        return;
    }

    signature_length = signature_capacity;
    if (!sign_once(key, algorithm, message, message_length, signature, &signature_length) ||
        !verify_once(key, algorithm, message, message_length, signature, signature_length)) {
        printf("%s,unsupported,EVP sign or verify failed,,,,,,%zu,\n", algorithm->name, message_length);
        OPENSSL_free(signature);
        OPENSSL_free(message);
        EVP_PKEY_free(key);
        fflush(stdout);
        return;
    }

    sign_start = monotonic_seconds();
    for (index = 0; index < iterations; index++) {
        signature_length = signature_capacity;
        if (!sign_once(key, algorithm, message, message_length, signature, &signature_length)) {
            printf("%s,unsupported,sign failed at iteration %llu,,,,,,%zu,\n",
                   algorithm->name, (unsigned long long)index, message_length);
            OPENSSL_free(signature);
            OPENSSL_free(message);
            EVP_PKEY_free(key);
            fflush(stdout);
            return;
        }
    }
    sign_seconds = monotonic_seconds() - sign_start;

    verify_start = monotonic_seconds();
    for (index = 0; index < iterations; index++) {
        if (!verify_once(key, algorithm, message, message_length, signature, signature_length)) {
            printf("%s,unsupported,verify failed at iteration %llu,,,,,,%zu,\n",
                   algorithm->name, (unsigned long long)index, message_length);
            OPENSSL_free(signature);
            OPENSSL_free(message);
            EVP_PKEY_free(key);
            fflush(stdout);
            return;
        }
    }
    verify_seconds = monotonic_seconds() - verify_start;

    getrusage(RUSAGE_SELF, &usage);
#ifdef __APPLE__
    long peak_rss_bytes = usage.ru_maxrss;
#else
    long peak_rss_bytes = usage.ru_maxrss * 1024L;
#endif
    printf("%s,confirmed,,%.9f,%.9f,%.9f,%zu,%llu,%zu,%ld\n",
           algorithm->name, keygen_seconds, sign_seconds, verify_seconds,
           signature_length, (unsigned long long)iterations, message_length, peak_rss_bytes);
    OPENSSL_free(signature);
    OPENSSL_free(message);
    EVP_PKEY_free(key);
    fflush(stdout);
}

int main(int argc, char **argv) {
    uint64_t iterations = 100000;
    size_t message_length = 32;
    size_t index;
    if (argc >= 2) {
        iterations = strtoull(argv[1], NULL, 10);
        if (iterations == 0) {
            fprintf(stderr, "iterations must be positive\n");
            return 2;
        }
    }
    if (argc >= 3) {
        message_length = (size_t)strtoull(argv[2], NULL, 10);
        if (message_length == 0) {
            fprintf(stderr, "message length must be positive\n");
            return 2;
        }
    }
    printf("algorithm,status,reason,keygen_seconds,sign_seconds,verify_seconds,signature_bytes,iterations,message_bytes,peak_rss_bytes\n");
    fflush(stdout);
    for (index = 0; index < sizeof(algorithms) / sizeof(algorithms[0]); index++) {
        benchmark(&algorithms[index], iterations, message_length);
    }
    return 0;
}
