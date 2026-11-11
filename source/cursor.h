#pragma once
#include <stdbool.h>
#include <math.h>

typedef struct { float x, y; bool visible, down, enabled; } NxCursor;

enum { NX_KEY_BACK = 1, NX_KEY_THROTTLE = 2, NX_KEY_BOOST = 4,
       NX_KEY_TILT_LEFT = 8, NX_KEY_TILT_RIGHT = 16, NX_KEY_EVENT_CAP = 10 };
typedef struct { int code; bool pressed; } NxKeyEvent;

static inline unsigned nx_controller_keys(const NxCursor *c, bool connected,
                                          bool a, bool x, bool b, float stick_x) {
    if (!connected) return 0;
    if (c->enabled) return b ? NX_KEY_BACK : 0;
    unsigned keys = (a ? NX_KEY_THROTTLE : 0) | (x ? NX_KEY_BOOST : 0) | (b ? NX_KEY_BACK : 0);
    if (isfinite(stick_x)) {
        if (stick_x < -0.25f) keys |= NX_KEY_TILT_LEFT;
        if (stick_x > 0.25f) keys |= NX_KEY_TILT_RIGHT;
    }
    return keys;
}

static inline int nx_key_changes(unsigned previous, unsigned current, NxKeyEvent out[NX_KEY_EVENT_CAP]) {
    const int codes[] = {4, 96, 99, 21, 22}; /* Android Back, Up, X, Left, Right. */
    int n = 0;
    for (int pressed = 0; pressed < 2; ++pressed)
        for (unsigned i = 0; i < sizeof(codes)/sizeof(codes[0]); ++i)
            if (((previous ^ current) & (1u << i)) && !!(current & (1u << i)) == pressed)
                out[n++] = (NxKeyEvent){codes[i], pressed != 0};
    return n;
}

static inline void nx_cursor_toggle(NxCursor *c) {
    c->enabled = !c->enabled;
    c->down = false;
    c->visible = false;
}

static inline float nx_cursor_axis(float v) {
    if (!isfinite(v) || fabsf(v) <= 0.18f) return 0;
    if (v > 1) v = 1;
    if (v < -1) v = -1;
    return copysignf((fabsf(v) - 0.18f) / 0.82f, v);
}

static inline void nx_cursor_step(NxCursor *c, float x, float y, float dt,
                                  bool connected, bool click, bool precise) {
    c->visible = connected && c->enabled;
    c->down = c->visible && click;
    if (!c->visible || !isfinite(dt) || dt <= 0) return;
    if (dt > 0.05f) dt = 0.05f;
    float speed = precise ? 180 : 720;
    c->x = fminf(1279, fmaxf(0, c->x + nx_cursor_axis(x) * dt * speed));
    c->y = fminf(719, fmaxf(0, c->y - nx_cursor_axis(y) * dt * speed));
}

/* Input publishes under its mutex; presentation may run on another thread. */
NxCursor nx_cursor_snapshot(void);
