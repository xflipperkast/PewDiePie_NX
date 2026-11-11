#pragma once
#include "runtime_base.h"
#ifdef __SWITCH__


/* Interface: module */


#include <elf.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <switch.h>


struct PdpLinker;

typedef enum PdpModuleState {
    PDP_MODULE_EMPTY = 0,
    PDP_MODULE_LOADED,
    PDP_MODULE_LAYOUT_READY,
    PDP_MODULE_RESERVED,
    PDP_MODULE_DYNAMIC_PARSED,
    PDP_MODULE_RELOCATING,
    PDP_MODULE_RELOCATED,
    PDP_MODULE_MAPPED,
    PDP_MODULE_CONSTRUCTED,
    PDP_MODULE_FINALIZED,
    PDP_MODULE_FAILED
} PdpModuleState;

typedef struct PdpRelocStats {
    size_t relative;
    size_t glob_dat;
    size_t jump_slot;
    size_t abs64;
    size_t relr;
    size_t tls_dtpmod;
    size_t tls_dtprel;
    size_t tls_tprel;
    size_t tlsdesc;
    size_t irelative;
    size_t ifunc;
    size_t weak_zero;
    size_t unresolved;
    size_t unsupported;
} PdpRelocStats;

typedef struct PdpTlsInfo {
    bool present;
    uint64_t vaddr;
    size_t file_size;
    size_t mem_size;
    size_t alignment;
    size_t module_id;
    ptrdiff_t static_offset;
    bool registered;
} PdpTlsInfo;

typedef struct PdpDynamicInfo {
    /*
     * Keep ELF virtual addresses as the canonical dynamic symbol/string-table
     * locations. Readers select the writable backing view before mapping and
     * the runtime alias after Horizon code-memory mapping.
     */
    uint64_t strtab_vaddr;
    size_t strsz;

    uint64_t symtab_vaddr;
    size_t syment;
    size_t symbol_count;

    Elf64_Rela *rela;
    size_t rela_count;

    /* Android packed RELA (APS2) is decoded at dynamic-parse time into owned
     * Elf64_Rela entries so the normal relocation engine remains canonical. */
    Elf64_Rela *android_rela;
    size_t android_rela_count;

    Elf64_Rela *jmprel;
    size_t jmprel_count;

    Elf64_Xword *relr;
    size_t relr_count;
    bool relr_is_android;

    uint64_t init_vaddr;
    uint64_t init_array_vaddr;
    size_t init_array_count;
    uint64_t fini_vaddr;
    uint64_t fini_array_vaddr;
    size_t fini_array_count;

    uint64_t hash_vaddr;
    uint64_t gnu_hash_vaddr;

    uint64_t versym_vaddr;
    uint64_t verneed_vaddr;
    size_t verneed_count;
    uint64_t verdef_vaddr;
    size_t verdef_count;

    uint32_t *needed_name_offsets;
    size_t needed_count;
    uint32_t soname_offset;

    /* Dynamic-linker policy bits. Android/Bionic uses DT_FLAGS_1/DF_1_GLOBAL
     * to build the process-wide global lookup group, and DT_SYMBOLIC or
     * DT_FLAGS/DF_SYMBOLIC to request local-first binding for definitions in
     * this DSO. Keep the raw flag words so the linker can reproduce that
     * policy without title-specific exceptions. */
    uint64_t flags;
    uint64_t flags_1;
    bool symbolic;
} PdpDynamicInfo;

typedef struct PdpModule {
    char path[0x200];

    void *file_image;
    size_t file_size;

    Elf64_Ehdr *ehdr;
    Elf64_Phdr *phdrs;
    Elf64_Shdr *shdrs;

    uint64_t min_vaddr;
    uint64_t max_vaddr;
    size_t image_size;

    void *backing;
    void *runtime_base;
    uintptr_t load_bias;
    struct PdpVmRange *reservation;
    bool mapped;
    bool post_map_relocations_applied;

    struct PdpLinker *linker;

    PdpDynamicInfo dynamic;
    PdpTlsInfo tls;
    PdpRelocStats reloc_stats;
    PdpModuleState state;
} PdpModule;

void pdp_module_init(PdpModule *module);
void pdp_module_unload(PdpModule *module);

void *pdp_module_runtime_address(const PdpModule *module, uint64_t elf_vaddr);
void *pdp_module_backing_address(const PdpModule *module, uint64_t elf_vaddr);
bool pdp_module_backing_contains(const PdpModule *module, uint64_t elf_vaddr, size_t size);
bool pdp_module_runtime_contains(const PdpModule *module, uintptr_t runtime_address, size_t size);


/* Interface: dynamic */


#include <stdbool.h>



PdpResult pdp_dynamic_parse(PdpModule *module);
PdpResult pdp_dynamic_run_constructors(PdpModule *module);
PdpResult pdp_dynamic_run_destructors(PdpModule *module);

/* Enable verbose AArch64 constructor tracing around real-APK bring-up.
 * Kept off for the retained Stage 1-12 fixtures so diagnostics do not alter
 * their normal output or timing. */
void pdp_dynamic_set_constructor_trace(bool enabled);

PdpResult pdp_dynamic_get_needed(const PdpModule *module, size_t index, const char **out_name);
PdpResult pdp_dynamic_get_soname(const PdpModule *module, const char **out_name);


/* Interface: symbols */


#include <elf.h>
#include <stdint.h>



typedef struct PdpSymbolVersion {
    const char *name;
    const char *provider; /* DT_VERNEED vn_file for imported versions. */
    uint32_t hash;
    bool hidden;
} PdpSymbolVersion;

typedef struct PdpResolvedSymbol {
    uintptr_t address;
    const char *name;
    PdpSymbolVersion version;
    const PdpModule *provider;
    unsigned type;
    bool weak_zero;
} PdpResolvedSymbol;

PdpResult pdp_symbol_get(const PdpModule *module, size_t symbol_index,
                             const Elf64_Sym **out_symbol, const char **out_name);
PdpResult pdp_symbol_resolve(PdpModule *module, size_t symbol_index,
                                 PdpResolvedSymbol *out);
/* Re-resolve a relocation symbol after mapping without recording a second
 * compatibility bind or relocation failure statistic. Used by the deferred
 * IFUNC pass, which revisits already-accounted relocations. */
PdpResult pdp_symbol_resolve_post_map(PdpModule *module, size_t symbol_index,
                                          PdpResolvedSymbol *out);
PdpResult pdp_symbol_probe(const PdpModule *module, size_t symbol_index,
                               const char **out_name, bool *out_weak_zero);

PdpResult pdp_symbol_version(const PdpModule *module, size_t symbol_index,
                                   PdpSymbolVersion *out_version);
PdpResult pdp_symbol_find_defined_versioned_ex(const PdpModule *module, const char *name,
                                                   const PdpSymbolVersion *required_version,
                                                   uintptr_t *out_address, unsigned *out_type);
PdpResult pdp_symbol_find_defined_versioned(const PdpModule *module, const char *name,
                                                const PdpSymbolVersion *required_version,
                                                uintptr_t *out_address);
PdpResult pdp_symbol_find_tls_defined_versioned(const PdpModule *module, const char *name,
                                                    const PdpSymbolVersion *required_version,
                                                    size_t *out_offset);
PdpResult pdp_symbol_resolve_tls(const PdpModule *requester, size_t symbol_index,
                                     const PdpModule **out_provider, size_t *out_offset,
                                     PdpSymbolVersion *out_version);
PdpResult pdp_symbol_find_defined(const PdpModule *module, const char *name,
                                      uintptr_t *out_address);


/* Interface: linker */


#include <stdbool.h>
#include <stddef.h>




typedef struct PdpLinkerNode PdpLinkerNode;

typedef struct PdpLinker {
    PdpLinkerNode **nodes;
    size_t node_count;
    size_t node_capacity;
    size_t compat_bind_count;
    char library_dir[0x200];
} PdpLinker;

void pdp_linker_init(PdpLinker *linker, const char *library_dir);
void pdp_linker_unload(PdpLinker *linker);

/* Load one root module plus its complete DT_NEEDED graph. */
PdpResult pdp_linker_load(PdpLinker *linker, const char *path, PdpModule **out_root);

/* Stage 14 Java Activity bootstrap may know the complete native root set before
 * Java executes the corresponding System.loadLibrary() calls. Discover the
 * union graph and reserve guest addresses only. Relocation, mapping,
 * .init/.init_array and JNI_OnLoad remain tied to the actual load operation so
 * unrelated RTLD_LOCAL roots cannot leak into one another's symbol scope. */
PdpResult pdp_linker_prepare_roots(PdpLinker *linker,
                                       const char *const *paths,
                                       size_t path_count,
                                       PdpModule **out_primary_root);

/* Run one already-mapped module's dependency constructors exactly once. Safe to
 * call repeatedly; dependencies are constructed before the requested module.
 * A constructor failure is latched: later calls return it without re-running. */
PdpResult pdp_linker_construct_module(PdpLinker *linker, const PdpModule *module);

/* True once the module's DT_INIT/DT_INIT_ARRAY have completed, i.e. once the
 * module is "loaded" in the Android-observable dlopen() sense. A module that
 * prepare_roots() mapped with deferred constructors reports false. */
bool pdp_linker_module_constructed(const PdpLinker *linker, const PdpModule *module);

/* Eager convenience path retained for NativeActivity and host tests: prepare the
 * complete graph, then construct every requested root in dependency order. */
PdpResult pdp_linker_load_roots(PdpLinker *linker,
                                    const char *const *paths,
                                    size_t path_count,
                                    PdpModule **out_primary_root);

/* Android System.loadLibrary() may request another root after the initial Java
 * bootstrap graph is already live. Add one lib*.so root to the existing graph
 * without relocating/reconstructing modules that are already loaded. */
PdpResult pdp_linker_load_library(PdpLinker *linker,
                                      const char *soname,
                                      PdpModule **out_module,
                                      bool *out_newly_loaded);

/* Resolve one undefined guest symbol against the loaded dependency scope. */
PdpResult pdp_linker_resolve_import_versioned(const PdpModule *requester,
                                                  const char *name,
                                                  const PdpSymbolVersion *version,
                                                  uintptr_t *out_address,
                                                  const PdpModule **out_provider);
PdpResult pdp_linker_resolve_import(const PdpModule *requester,
                                        const char *name,
                                        uintptr_t *out_address,
                                        const PdpModule **out_provider);

/* Side-effect-free import lookup used by relocation preflight. Unlike the
 * normal resolver it does not increment compatibility bind counters or emit
 * per-bind success logs. */
PdpResult pdp_linker_resolve_tls_import_versioned(const PdpModule *requester,
                                                      const char *name,
                                                      const PdpSymbolVersion *version,
                                                      const PdpModule **out_provider,
                                                      size_t *out_offset);

PdpResult pdp_linker_probe_import_versioned(const PdpModule *requester,
                                                const char *name,
                                                const PdpSymbolVersion *version,
                                                uintptr_t *out_address,
                                                const PdpModule **out_provider);
PdpResult pdp_linker_probe_import(const PdpModule *requester,
                                      const char *name,
                                      uintptr_t *out_address,
                                      const PdpModule **out_provider);

/* dlsym(handle, name) searches the handle's local dependency group, not just
 * the root object. Version is NULL for ordinary dlsym and non-NULL for future
 * dlvsym-style lookups. */
PdpResult pdp_linker_find_in_handle(const PdpLinker *linker,
                                        const PdpModule *module,
                                        const char *name,
                                        const PdpSymbolVersion *version,
                                        uintptr_t *out_address,
                                        const PdpModule **out_provider);
PdpResult pdp_linker_find_global(const PdpLinker *linker,
                                     const char *name,
                                     const PdpSymbolVersion *version,
                                     uintptr_t *out_address,
                                     const PdpModule **out_provider);

/* Stable dlopen handle lifetime. Java/System.loadLibrary roots are pinned;
 * native dlopen references are counted and dlclose runs eligible destructors. */
PdpResult pdp_linker_acquire_module(PdpLinker *linker, const PdpModule *module);
PdpResult pdp_linker_release_module(PdpLinker *linker, const PdpModule *module);
PdpResult pdp_linker_pin_module(PdpLinker *linker, const PdpModule *module);
bool pdp_linker_module_handle_live(const PdpLinker *linker, const PdpModule *module);

/* Resolve only against Bionic's process-wide guest global group. Used when a
 * relocation references a default-visibility symbol defined by the requester:
 * such a definition is preemptible unless the DSO requested symbolic binding
 * or the symbol is STV_PROTECTED. */
PdpResult pdp_linker_probe_global_versioned(const PdpModule *requester,
                                                const char *name,
                                                const PdpSymbolVersion *version,
                                                uintptr_t *out_address,
                                                const PdpModule **out_provider);
PdpResult pdp_linker_probe_global(const PdpModule *requester,
                                      const char *name,
                                      uintptr_t *out_address,
                                      const PdpModule **out_provider);

/* dlopen(..., RTLD_GLOBAL) promotes an already-loaded local root so its symbols
 * are visible to later loads. DF_1_GLOBAL modules are promoted automatically. */
PdpResult pdp_linker_promote_global(PdpLinker *linker,
                                        const PdpModule *module,
                                        const char *reason);

size_t pdp_linker_module_count(const PdpLinker *linker);
size_t pdp_linker_compat_bind_count(const PdpLinker *linker);
const PdpModule *pdp_linker_module_at(const PdpLinker *linker, size_t index);


/* Interface: loader */



/* Generic single-module loader retained for Stage 1/2 regression tests. */
PdpResult pdp_loader_load(const char *path, PdpModule *module);

/* Stage 1 regression path: succeeds only when the guest requires no relocations. */
PdpResult pdp_loader_load_stage1(const char *path, PdpModule *module);

PdpResult pdp_loader_find_export(const PdpModule *module, const char *name, void **out_address);

/* Stage 3 linker building blocks. These do not run constructors implicitly. */
PdpResult pdp_loader_prepare(const char *path, PdpModule *module);
/* Header-only classification for speculative Java native-library candidates. */
PdpResult pdp_loader_probe_shared_object(const char *path, bool *out_shared);
PdpResult pdp_loader_relocate(PdpModule *module);
PdpResult pdp_loader_patch_system_registers(PdpModule *module);
PdpResult pdp_loader_map(PdpModule *module);
PdpResult pdp_loader_resolve_ifuncs(PdpModule *module);
PdpResult pdp_loader_construct(PdpModule *module);


/* Interface: relocations */



PdpResult pdp_apply_relr(PdpModule *module);
PdpResult pdp_preflight_relocations(PdpModule *module, size_t *out_unique_missing);
PdpResult pdp_apply_relocations(PdpModule *module);
PdpResult pdp_apply_post_map_relocations(PdpModule *module);


#endif /* __SWITCH__ */
