"""Ported DGA families. Each module has PERIOD_DAYS and generate(day, count)."""

from dgadetect.dga import necurs, pushdo, qakbot, suppobox

FAMILIES = {
    "necurs": necurs,
    "qakbot": qakbot,
    "pushdo": pushdo,
    "suppobox": suppobox,
}
