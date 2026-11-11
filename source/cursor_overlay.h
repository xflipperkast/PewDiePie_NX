#pragma once
#include "cursor.h"

/* Scissored clears need no shader, texture, vertex array or new GL context.
 * Khronos ES 2 section 4.2.3: scissor and color masks affect glClear. */
static void nx_cursor_draw(EGLDisplay display, int width, int height) {
    NxCursor c = nx_cursor_snapshot();
    static int previous_status = -2;
    int status = !c.visible ? 0 : width > 0 && height > 0 ? 1 : -1;
    if (status != previous_status) {
        PDP_LOGCI("CURSOR", "overlay revision=cursor-3 thread=%lx status=%s physical=%dx%d",
                    (unsigned long)pthread_self(), status == 1 ? "draw" : status == 0 ? "hidden" : "invalid-size", width, height);
        previous_status = status;
    }
    if (status != 1) {
        return;
    }
    EGLint version = 2;
    eglQueryContext(display, eglGetCurrentContext(), EGL_CONTEXT_CLIENT_VERSION, &version);
    GLenum target = version >= 3 ? GL_DRAW_FRAMEBUFFER : GL_FRAMEBUFFER;
    GLint framebuffer, box[4];
    GLfloat color[4];
    GLboolean mask[4], scissor = glIsEnabled(GL_SCISSOR_TEST);
    GLboolean discard = version >= 3 ? glIsEnabled(GL_RASTERIZER_DISCARD) : GL_FALSE;
    glGetIntegerv(GL_FRAMEBUFFER_BINDING, &framebuffer);
    glGetIntegerv(GL_SCISSOR_BOX, box);
    glGetFloatv(GL_COLOR_CLEAR_VALUE, color);
    glGetBooleanv(GL_COLOR_WRITEMASK, mask);
    glBindFramebuffer(target, 0);
    if (version >= 3) glDisable(GL_RASTERIZER_DISCARD);
    glEnable(GL_SCISSOR_TEST);
    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);
    int x = (int)(c.x * (width - 1) / 1279.0f);
    int y = height - 1 - (int)(c.y * (height - 1) / 719.0f);
    glClearColor(0, 0, 0, 1);
    glScissor(x - 9, y - 3, 19, 7); glClear(GL_COLOR_BUFFER_BIT);
    glScissor(x - 3, y - 9, 7, 19); glClear(GL_COLOR_BUFFER_BIT);
    glClearColor(1, c.down ? 0.6f : 1, c.down ? 0 : 1, 1);
    glScissor(x - 8, y - 1, 17, 3); glClear(GL_COLOR_BUFFER_BIT);
    glScissor(x - 1, y - 8, 3, 17); glClear(GL_COLOR_BUFFER_BIT);
    glClearColor(color[0], color[1], color[2], color[3]);
    glColorMask(mask[0], mask[1], mask[2], mask[3]);
    glScissor(box[0], box[1], box[2], box[3]);
    if (!scissor) glDisable(GL_SCISSOR_TEST);
    if (discard) glEnable(GL_RASTERIZER_DISCARD);
    glBindFramebuffer(target, (GLuint)framebuffer);
}
