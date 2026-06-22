#include <openssl/evp.h>
#include <openssl/rsa.h>
#include <oqs/oqs.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

enum backend { BACKEND_EVP, BACKEND_OQS };

struct component_spec {
    const char *name;
    enum backend backend;
    const char *key_type;
    const char *digest;
    const char *group;
    int rsa_bits;
};

struct component {
    const struct component_spec *spec;
    EVP_PKEY *evp_key;
    OQS_SIG *oqs;
    unsigned char *public_key;
    unsigned char *secret_key;
    unsigned char *signature;
    size_t signature_capacity;
    size_t signature_length;
    size_t maximum_signature_length;
};

struct combination {
    const char *name;
    const struct component_spec *first;
    const struct component_spec *second;
};

static const struct component_spec rsa = {
    "RSA-2048/SHA-256", BACKEND_EVP, "RSA", "SHA256", NULL, 2048
};
static const struct component_spec p256 = {
    "P-256/SHA-256", BACKEND_EVP, "EC", "SHA256", "P-256", 0
};
static const struct component_spec mldsa44 = {
    "ML-DSA-44", BACKEND_EVP, "ML-DSA-44", NULL, NULL, 0
};
static const struct component_spec mldsa65 = {
    "ML-DSA-65", BACKEND_EVP, "ML-DSA-65", NULL, NULL, 0
};
static const struct component_spec mldsa87 = {
    "ML-DSA-87", BACKEND_EVP, "ML-DSA-87", NULL, NULL, 0
};
static const struct component_spec falcon512 = {
    "Falcon-512", BACKEND_OQS, "Falcon-512", NULL, NULL, 0
};

static const struct combination combinations[] = {
    {"RSA-2048+ML-DSA-44", &rsa, &mldsa44},
    {"P-256+ML-DSA-44", &p256, &mldsa44},
    {"RSA-2048+ML-DSA-65", &rsa, &mldsa65},
    {"P-256+ML-DSA-65", &p256, &mldsa65},
    {"RSA-2048+ML-DSA-87", &rsa, &mldsa87},
    {"P-256+ML-DSA-87", &p256, &mldsa87},
    {"P-256+Falcon-512", &p256, &falcon512},
};

static double monotonic_seconds(void) {
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value) != 0) {
        return -1.0;
    }
    return (double)value.tv_sec + (double)value.tv_nsec / 1000000000.0;
}

static EVP_PKEY *generate_evp_key(const struct component_spec *spec) {
    EVP_PKEY_CTX *context = EVP_PKEY_CTX_new_from_name(NULL, spec->key_type, NULL);
    EVP_PKEY *key = NULL;
    if (context == NULL || EVP_PKEY_keygen_init(context) <= 0) {
        EVP_PKEY_CTX_free(context);
        return NULL;
    }
    if (spec->rsa_bits && EVP_PKEY_CTX_set_rsa_keygen_bits(context, spec->rsa_bits) <= 0) {
        EVP_PKEY_CTX_free(context);
        return NULL;
    }
    if (spec->group && EVP_PKEY_CTX_set_group_name(context, spec->group) <= 0) {
        EVP_PKEY_CTX_free(context);
        return NULL;
    }
    if (EVP_PKEY_generate(context, &key) <= 0) {
        key = NULL;
    }
    EVP_PKEY_CTX_free(context);
    return key;
}

static int initialize_component(struct component *component, const struct component_spec *spec) {
    memset(component, 0, sizeof(*component));
    component->spec = spec;
    if (spec->backend == BACKEND_EVP) {
        component->evp_key = generate_evp_key(spec);
        if (component->evp_key == NULL) {
            return 0;
        }
        component->signature_capacity = (size_t)EVP_PKEY_get_size(component->evp_key);
    } else {
        component->oqs = OQS_SIG_new(spec->key_type);
        if (component->oqs == NULL) {
            return 0;
        }
        component->public_key = OQS_MEM_malloc(component->oqs->length_public_key);
        component->secret_key = OQS_MEM_malloc(component->oqs->length_secret_key);
        component->signature_capacity = component->oqs->length_signature;
        if (component->public_key == NULL || component->secret_key == NULL ||
            OQS_SIG_keypair(component->oqs, component->public_key, component->secret_key) != OQS_SUCCESS) {
            return 0;
        }
    }
    component->signature = OQS_MEM_malloc(component->signature_capacity);
    return component->signature != NULL;
}

static int sign_component(struct component *component, const unsigned char *message, size_t message_length) {
    component->signature_length = component->signature_capacity;
    if (component->spec->backend == BACKEND_EVP) {
        EVP_MD_CTX *context = EVP_MD_CTX_new();
        int result = context != NULL &&
            EVP_DigestSignInit_ex(context, NULL, component->spec->digest, NULL, NULL,
                                  component->evp_key, NULL) > 0 &&
            EVP_DigestSign(context, component->signature, &component->signature_length,
                           message, message_length) > 0;
        EVP_MD_CTX_free(context);
        if (!result) {
            return 0;
        }
    } else if (OQS_SIG_sign(component->oqs, component->signature, &component->signature_length,
                            message, message_length, component->secret_key) != OQS_SUCCESS) {
        return 0;
    }
    if (component->signature_length > component->maximum_signature_length) {
        component->maximum_signature_length = component->signature_length;
    }
    return 1;
}

static int verify_component(struct component *component, const unsigned char *message, size_t message_length) {
    if (component->spec->backend == BACKEND_EVP) {
        EVP_MD_CTX *context = EVP_MD_CTX_new();
        int result = context != NULL &&
            EVP_DigestVerifyInit_ex(context, NULL, component->spec->digest, NULL, NULL,
                                    component->evp_key, NULL) > 0 &&
            EVP_DigestVerify(context, component->signature, component->signature_length,
                             message, message_length) == 1;
        EVP_MD_CTX_free(context);
        return result;
    }
    return OQS_SIG_verify(component->oqs, message, message_length,
                          component->signature, component->signature_length,
                          component->public_key) == OQS_SUCCESS;
}

static void free_component(struct component *component) {
    EVP_PKEY_free(component->evp_key);
    if (component->secret_key != NULL && component->oqs != NULL) {
        OQS_MEM_cleanse(component->secret_key, component->oqs->length_secret_key);
    }
    OQS_MEM_insecure_free(component->public_key);
    OQS_MEM_insecure_free(component->secret_key);
    OQS_MEM_insecure_free(component->signature);
    OQS_SIG_free(component->oqs);
}

static void benchmark(const struct combination *combination, uint64_t iterations) {
    static const unsigned char message[32] = {
        0x70, 0x71, 0x63, 0x2d, 0x72, 0x70, 0x6b, 0x69,
        0x2d, 0x63, 0x6f, 0x6d, 0x70, 0x6f, 0x73, 0x69,
        0x74, 0x65, 0x2d, 0x31, 0x30, 0x30, 0x6b, 0x2d,
        0x62, 0x65, 0x6e, 0x63, 0x68, 0x2d, 0x76, 0x31
    };
    struct component first, second;
    uint64_t index;
    double start, sign_seconds, verify_seconds;

    memset(&first, 0, sizeof(first));
    memset(&second, 0, sizeof(second));
    if (!initialize_component(&first, combination->first) ||
        !initialize_component(&second, combination->second)) {
        printf("%s,unsupported,component initialization failed,,,,,,\n", combination->name);
        fflush(stdout);
        free_component(&first);
        free_component(&second);
        return;
    }
    if (!sign_component(&first, message, sizeof(message)) ||
        !sign_component(&second, message, sizeof(message)) ||
        !verify_component(&first, message, sizeof(message)) ||
        !verify_component(&second, message, sizeof(message))) {
        printf("%s,unsupported,component smoke test failed,,,,,,\n", combination->name);
        fflush(stdout);
        free_component(&first);
        free_component(&second);
        return;
    }

    start = monotonic_seconds();
    for (index = 0; index < iterations; index++) {
        if (!sign_component(&first, message, sizeof(message)) ||
            !sign_component(&second, message, sizeof(message))) {
            printf("%s,unsupported,sign failed at iteration %llu,,,,,,\n",
                   combination->name, (unsigned long long)index);
            fflush(stdout);
            free_component(&first);
            free_component(&second);
            return;
        }
    }
    sign_seconds = monotonic_seconds() - start;

    start = monotonic_seconds();
    for (index = 0; index < iterations; index++) {
        if (!verify_component(&first, message, sizeof(message)) ||
            !verify_component(&second, message, sizeof(message))) {
            printf("%s,unsupported,verify failed at iteration %llu,,,,,,\n",
                   combination->name, (unsigned long long)index);
            fflush(stdout);
            free_component(&first);
            free_component(&second);
            return;
        }
    }
    verify_seconds = monotonic_seconds() - start;

    printf("%s,confirmed,,%llu,%.9f,%.9f,%zu,%zu,%zu\n",
           combination->name, (unsigned long long)iterations, sign_seconds, verify_seconds,
           first.maximum_signature_length, second.maximum_signature_length,
           first.maximum_signature_length + second.maximum_signature_length);
    fflush(stdout);
    free_component(&first);
    free_component(&second);
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
    printf("algorithm,status,reason,iterations,sign_seconds,verify_seconds,component1_signature_max_bytes,component2_signature_max_bytes,combined_signature_bytes\n");
    fflush(stdout);
    for (index = 0; index < sizeof(combinations) / sizeof(combinations[0]); index++) {
        benchmark(&combinations[index], iterations);
    }
    return 0;
}
