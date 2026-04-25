"""Known x402 facilitator addresses on Base. Updated 2026-04-25 via Dune."""

CDP_FACILITATOR_POOL = {
    "0x8f5cb67b49555e614892b7233cfddebfb746e531",
    "0x68a96f41ff1e9f2e7b591a931a4ad224e7c07863",
    "0xa32ccda98ba7529705a059bd2d213da8de10d101",
    "0x97acce27d5069544480bde0f04d9f47d7422a016",
    "0x67b9ce703d9ce658d7c4ac3c289cea112fe662af",
}

OTHER_FACILITATORS = {
    "0xd2f74a14522d40e4a1d7fbb62aa97ce99fa1a7e5",  # ~10k tx/wk — likely Bankr or PayAI
    "0xe5588c407b6add3e83ce34190c77de20eac1befe",  # ~2k tx/wk
    "0x37dfb4033d5dd98fd335f24d0d42e8fe68d587d6",
    "0x66c40946b0dffd04be467e18309857307ecd37cb",
    "0x6cb960c17a623575dd8db626899c0645ed30e3d5",
}

ALL_FACILITATORS = CDP_FACILITATOR_POOL | OTHER_FACILITATORS


def is_facilitator(addr: str) -> bool:
    return addr.lower() in ALL_FACILITATORS


def facilitator_label(addr: str) -> str | None:
    a = addr.lower()
    if a in CDP_FACILITATOR_POOL:
        return "cdp"
    if a in OTHER_FACILITATORS:
        return "other"
    return None
