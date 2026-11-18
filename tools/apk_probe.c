#include "runtime_base.h"
#include <stdarg.h>
#include <stdio.h>

/* Keep the host importer on the same production manifest/bootstrap reader. */
void pdp_log(const char *level, const char *fmt, ...) { (void)level; (void)fmt; }
bool pdp_diag_full_trace_enabled(void) { return false; }
void pdp_log_category(const char *cat, const char *level, const char *fmt, ...) {
    (void)cat; (void)level; (void)fmt;
}
static void string(const char *p) {
    putchar('"');
    for (; *p; ++p) {
        unsigned char c = (unsigned char)*p;
        if (c == '"' || c == '\\') putchar('\\');
        if (c < 32 || c >= 127) printf("\\u%04x", c); else putchar(c);
    }
    putchar('"');
}
int main(int argc, char **argv) {
    if (argc != 2 && argc != 3) return 2;
    PdpApkInfo info = {0};
    PdpResult rc = pdp_package_probe(argv[1], &info);
    if (argc == 3) {
        uint32_t *pixels = NULL;
        int w = 0, h = 0;
        char source[512] = {0};
        PdpResult icon_rc = pdp_apk_load_launcher_icon(argv[1], &pixels, &w, &h, source, sizeof(source));
        if (icon_rc != PDP_OK) return 3;
        FILE *out = fopen(argv[2], "wb");
        if (!out) return 4;
        bool ok = fwrite(&w, 4, 1, out) == 1 && fwrite(&h, 4, 1, out) == 1 &&
                  fwrite(pixels, 4, (size_t)w*h, out) == (size_t)w*h;
        if (fclose(out)) ok = false;
        if (!ok) return 5;
        fprintf(stderr, "Manifest launcher icon: %s (%dx%d)\n", source, w, h);
    }
    printf("{\"result\":%d,\"package\":", rc); string(info.package_name);
    printf(",\"activity\":"); string(info.activity_name);
    printf(",\"version\":"); string(info.version_name);
    printf(",\"arm64_libraries\":%zu,\"dex_files\":%zu,\"java_bootstrap\":%s,\"native_activity\":%s}\n",
           info.arm64_lib_count, info.java_dex_count,
           info.java_activity_bootstrap ? "true" : "false", info.native_activity ? "true" : "false");
    return 0;
}
