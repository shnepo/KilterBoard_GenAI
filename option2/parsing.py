import re

V_SCALE = {
    "V0": 0.05, "V1": 0.10, "V2": 0.15,
    "V3": 0.25, "V4": 0.35, "V5": 0.45,
    "V6": 0.55, "V7": 0.60, "V8": 0.70,
    "V9": 0.78, "V10": 0.85, "V11": 0.92,
    "V12": 0.96, "V13": 0.98, "V14": 1.00
}

FB_SCALE = {
    "5A": 0.10, "5B": 0.15, "5C": 0.20,
    "6A": 0.30, "6A+": 0.35,
    "6B": 0.40, "6B+": 0.45,
    "6C": 0.50, "6C+": 0.55,
    "7A": 0.60, "7A+": 0.65,
    "7B": 0.70, "7B+": 0.75,
    "7C": 0.80, "7C+": 0.85,
    "8A": 0.90, "8A+": 0.93,
    "8B": 0.96, "8B+": 0.98,
    "8C": 1.00
}


def parse_style(style_input: str):
    """
    Convert user style text ('crimpy, technical, powerful, compression, dyno, big moves, hips, ect') 
    into numerical parameters for generation.
    """

    style_input = style_input.lower()

    params = {
        "hold_size_preference": 0.5,       # 0 = tiny holds, 1 = big holds
        "avg_move_distance": 0.5,          # 0 = very close, 1 = far
        "compression_level": 0.0,          # 0 = none, 1 = lots
        "crimpy_level": 0.0,               # 0 = slopers, 1 = crimps
        "footwork_technicality": 0.5,      # 0 = simple, 1 = techy
        "dynamic_level": 0.5               # 0 = static, 1 = dyno
    }

    # --- Keyword-based adjustments ---

    # Better more fool-proof system can be implemented later
    
    if "crimp" in style_input or "crimpy" in style_input:
        params["crimpy_level"] = 0.9
        params["hold_size_preference"] = 0.2

    if "sloper" in style_input or "slopey" in style_input:
        params["crimpy_level"] = 0.1
        params["hold_size_preference"] = 0.8

    if "compression" in style_input:
        params["compression_level"] = 0.9

    if "dynamic" in style_input or "dyno" in style_input or "powerful" in style_input:
        params["dynamic_level"] = 0.8
        params["avg_move_distance"] = 0.7

    if "technical" in style_input or "techy" in style_input or "balance" in style_input:
        params["footwork_technicality"] = 0.8
        params["avg_move_distance"] = 0.3

    if "big moves" in style_input or "reachy" in style_input:
        params["avg_move_distance"] = 0.9

    return params


def parse_difficulty(diff_input: str) -> float:
    """
    Convert a user difficulty input ('V4', '6B+', 'soft 7A') 
    into a normalized difficulty value.
    """

    text = diff_input.strip().upper()

    # Handle soft/hard modifiers
    soft = "SOFT" in text
    hard = "HARD" in text

    # Remove words
    text = text.replace("SOFT", "").replace("HARD", "").strip()

    # Detect V-scale
    v_match = re.match(r"V(\d+)", text)
    if v_match:
        grade = "V" + v_match.group(1)
        if grade in V_SCALE:
            base = V_SCALE[grade]
            if soft: base -= 0.03
            if hard: base += 0.03
            return max(0.0, min(1.0, base))

    # Detect Fontainebleau
    fb_grade = text
    if fb_grade in FB_SCALE:
        base = FB_SCALE[fb_grade]
        if soft: base -= 0.03
        if hard: base += 0.03
        return max(0.0, min(1.0, base))

    # Grade ranges ("V3-V5", "6A-6C")
    range_match = re.match(r"(.+)[\-–](.+)", text)
    if range_match:
        g1, g2 = range_match.group(1).strip(), range_match.group(2).strip()
        vals = []
        for g in (g1, g2):
            if g.startswith("V") and g in V_SCALE:
                vals.append(V_SCALE[g])
            elif g in FB_SCALE:
                vals.append(FB_SCALE[g])
        if vals:
            return sum(vals) / len(vals)

    # Default fallback (very easy)
    return 0.15
