def CLIP(X):
    if X > 255:
        return 255
    elif X < 0:
        return 0
    return X

# YUV -> RGB
def C(Y): return ((Y)-16)
def D(U): return ((U)-128)
def E(V): return ((V)-128)


def YUV2R(Y, U, V):
    return CLIP((298 * C(Y) + 409 * E(V) + 128) >> 8)


def YUV2G(Y, U, V):
    return CLIP((298 * C(Y) - 100 * D(U) - 208 * E(V) + 128) >> 8)


def YUV2B(Y, U, V):
    return CLIP((298 * C(Y) + 516 * D(U) + 128) >> 8)

