"""Focused unit tests for the port manager parsing helpers."""
import port_manager as pm

# IPv6 addresses are bracketed, so the port comes from the last colon.
print("IPv6 ->", pm.parse_netstat("TCP    [::]:135    [::]:0    LISTENING    1756"))
print("UDP  ->", pm.parse_netstat("UDP    0.0.0.0:53    *:*    3676"))

# Header and blank lines must be ignored rather than crashing.
print("hdrs ->", pm.parse_netstat("Active Connections\n\n  Proto  Local Address  Foreign Address  State  PID"))
print("junk ->", pm.parse_netstat("TCP    bad"))
print("none ->", pm.parse_netstat(""), pm.parse_netstat(None))

sample_tasklist = (
    '"System Idle Process","0","Services","0","8 K"\n'
    '"node.exe","1234","Console","1","5,000 K"\n'
    '"broken","notanumber","Console","1","1 K"\n'
)
print("tasklist ->", sorted(pm.parse_tasklist(sample_tasklist).items()))
print("tl none ->", pm.parse_tasklist(""), pm.parse_tasklist(None))

record = {
    "proto": "TCP", "local_address": "0.0.0.0", "local_port": "8080",
    "remote_address": "0.0.0.0", "remote_port": "0",
    "state": "LISTENING", "pid": 5,
}
print("filter All/8080 ->", pm.record_matches(record, "All", "8080"))
print("filter TCP/8080 ->", pm.record_matches(record, "TCP", "8080"))
print("filter UDP/8080 ->", pm.record_matches(record, "UDP", "8080"))
print("filter All/listening ->", pm.record_matches(record, "All", "listening"))

print("protected pid 4/System ->", pm.is_protected(4, "System"))
print("protected pid 0/None ->", pm.is_protected(0, None))
print("protected node.exe ->", pm.is_protected(5, "node.exe"))
print("protected lsass.exe ->", pm.is_protected(9, "LSASS.EXE"))
print("summary ->", pm.format_summary([record]))
print("filter summary ->", pm.filter_summary([record], 1), pm.filter_summary([], 9))