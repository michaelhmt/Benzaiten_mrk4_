from os.path import normpath, join


def norman_path(*parts: str) -> str:
    """
    Take path parts and return a joined
    and normalized filepath.
    """

    return normpath(join(*[str(p) for p in parts]))
