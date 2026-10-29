import subprocess
import sys
import textwrap

PROBE = textwrap.dedent(
    """
    import kadishutu._frozen as frozen
    from kadishutu.tools import depinstall
    from kadishutu.tools.depinstall import generic

    frozen.apply()

    for handler in (depinstall.get_install_handler, generic.get_install_handler):
        try:
            handler()
        except NotImplementedError:
            pass
        else:
            raise SystemExit("frozen build still exposes an install handler")

    if generic.INSTALL_HANDLERS:
        raise SystemExit("frozen build still lists install handlers")
    """
)


def test_apply_disables_install_handlers():
    # Run in a subprocess: apply() patches module globals, which would leak
    # into the rest of the test session.
    subprocess.run([sys.executable, "-c", PROBE], check=True)
