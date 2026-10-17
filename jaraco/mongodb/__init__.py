import sys

if sys.platform == 'win32':  # pragma: no cover
    # Resolve nameservers only from active interfaces (rthalley/dnspython#1191)
    # without requiring WMI and pywin32 (jaraco/jaraco.mongodb#47).
    import dns.win32util

    dns.win32util.set_config_method(dns.win32util.ConfigMethod.Win32)
