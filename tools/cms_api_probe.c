#include <openssl/cms.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/x509.h>

#include <stdio.h>
#include <string.h>

static void errors(void) {
    ERR_print_errors_fp(stderr);
}

int main(int argc, char **argv) {
    BIO *key_bio = NULL, *cert_bio = NULL, *data = NULL, *output = NULL;
    EVP_PKEY *key = NULL;
    X509 *cert = NULL;
    CMS_ContentInfo *cms = NULL;
    CMS_SignerInfo *signer = NULL;
    ASN1_OBJECT *content_type = NULL;
    const EVP_MD *digest = NULL;
    int flags = CMS_BINARY | CMS_NOSMIMECAP;
    int status = 1;

    if (argc != 7 || (strcmp(argv[1], "default") != 0 && strcmp(argv[1], "sha512") != 0)) {
        fprintf(stderr, "usage: %s default|sha512 KEY CERT CONTENT ECONTENT_OID OUTPUT\n", argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "sha512") == 0)
        digest = EVP_sha512();
    key_bio = BIO_new_file(argv[2], "r");
    cert_bio = BIO_new_file(argv[3], "r");
    data = BIO_new_file(argv[4], "rb");
    output = BIO_new_file(argv[6], "wb");
    if (!key_bio || !cert_bio || !data || !output)
        goto done;
    key = PEM_read_bio_PrivateKey(key_bio, NULL, NULL, NULL);
    cert = PEM_read_bio_X509(cert_bio, NULL, NULL, NULL);
    content_type = OBJ_txt2obj(argv[5], 1);
    cms = CMS_sign(NULL, NULL, NULL, NULL, flags | CMS_PARTIAL);
    if (!key || !cert || !content_type || !cms || !CMS_set1_eContentType(cms, content_type))
        goto done;
    signer = CMS_add1_signer(cms, cert, key, digest, flags | CMS_USE_KEYID);
    if (!signer || !CMS_final(cms, data, NULL, flags) || !i2d_CMS_bio(output, cms))
        goto done;
    status = 0;
done:
    if (status != 0)
        errors();
    ASN1_OBJECT_free(content_type);
    CMS_ContentInfo_free(cms);
    X509_free(cert);
    EVP_PKEY_free(key);
    BIO_free(output);
    BIO_free(data);
    BIO_free(cert_bio);
    BIO_free(key_bio);
    return status;
}
