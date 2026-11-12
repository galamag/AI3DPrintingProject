"""print_mcp.profiles: reading Bambu Studio profiles and their `inherits` chains."""
from __future__ import annotations

import json

import pytest

from print_mcp.profiles import ProfileNotFound, list_profiles, load_profile, profile_path


def _write(root, kind, name, **data):
    folder = root / kind
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"type": kind, "name": name, **data}
    (folder / f"{name}.json").write_text(json.dumps(payload, indent=4), encoding="utf-8")


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "BBL"

    _write(root, "machine", "fdm_machine_common", instantiation="false",
           nozzle_diameter=["0.4"], printable_height="250")
    _write(root, "machine", "Bambu Lab P2S 0.4 nozzle", inherits="fdm_machine_common",
           instantiation="true", printable_height="256")
    _write(root, "machine", "Bambu Lab P2S 0.2 nozzle", inherits="fdm_machine_common",
           instantiation="true", nozzle_diameter=["0.2"])
    _write(root, "machine", "Bambu Lab P2S 0.4 nozzle template machine_start_gcode",
           instantiation="false", machine_start_gcode="G28")

    _write(root, "process", "fdm_process_common", instantiation="false",
           layer_height="0.2", wall_loops="2", sparse_infill_density="15%")
    _write(root, "process", "0.20mm Standard @BBL P2S", inherits="fdm_process_common",
           instantiation="true", description="Standard profile", sparse_infill_density="20%")
    _write(root, "process", "0.10mm Standard @BBL P2S 0.2 nozzle", inherits="fdm_process_common",
           instantiation="true", layer_height="0.1")
    _write(root, "process", "0.30mm Standard @BBL P2S 0.6 nozzle", inherits="fdm_process_common",
           instantiation="true", layer_height="0.3")
    _write(root, "process", "0.20mm Template @BBL P2S", inherits="fdm_process_common",
           instantiation="false")
    _write(root, "process", "0.20mm Standard @BBL P2SC", inherits="fdm_process_common",
           instantiation="true")
    _write(root, "process", "0.20mm Standard @BBL X1C", inherits="fdm_process_common",
           instantiation="true")

    _write(root, "filament", "fdm_filament_common", instantiation="false",
           filament_density=["1.24"], nozzle_temperature=["200"], filament_type=["PLA"],
           nozzle_temperature_range_low=["190"], nozzle_temperature_range_high=["240"])
    _write(root, "filament", "Bambu PLA Lite @base", inherits="fdm_filament_common",
           instantiation="false", filament_density=["1.40"], textured_plate_temp=["55"])
    _write(root, "filament", "Bambu PLA Lite @BBL P2S 0.4 nozzle", inherits="Bambu PLA Lite @base",
           instantiation="true", nozzle_temperature=["220", "220", "220"],
           filament_max_volumetric_speed=["16", "40", "16"])
    _write(root, "filament", "Bambu PLA Lite @BBL P2S 0.2 nozzle", inherits="Bambu PLA Lite @base",
           instantiation="true")
    _write(root, "filament", "Bambu PETG HF @BBL P2S", inherits="fdm_filament_common",
           instantiation="true", filament_type=["PETG"])
    return root


def _names(entries):
    return [entry["name"] for entry in entries]


# --- load_profile -----------------------------------------------------------


def test_child_overrides_parent_and_parent_keys_stay_visible(tree):
    profile = load_profile("process", "0.20mm Standard @BBL P2S", root=tree)
    assert profile["sparse_infill_density"] == "20%"
    assert profile["layer_height"] == "0.2"
    assert profile["wall_loops"] == "2"
    assert profile["name"] == "0.20mm Standard @BBL P2S"


def test_three_level_chain(tree):
    profile = load_profile("filament", "Bambu PLA Lite @BBL P2S 0.4 nozzle", root=tree)
    assert profile["filament_density"] == ["1.40"]
    assert profile["nozzle_temperature"] == ["220", "220", "220"]
    assert profile["nozzle_temperature_range_low"] == ["190"]


@pytest.mark.parametrize("name", ["..\\x", "a/b", "a;b", "", "..", "C:x"])
def test_bad_names_are_rejected(tree, name):
    with pytest.raises(ValueError):
        load_profile("process", name, root=tree)
    with pytest.raises(ValueError):
        profile_path("process", name, root=tree)


def test_unknown_kind_is_rejected(tree):
    with pytest.raises(ValueError):
        load_profile("printer", "Bambu Lab P2S 0.4 nozzle", root=tree)


def test_unknown_name_raises_profile_not_found(tree):
    with pytest.raises(ProfileNotFound):
        load_profile("process", "0.99mm Missing @BBL P2S", root=tree)
    assert issubclass(ProfileNotFound, LookupError)


def test_missing_parent_raises_profile_not_found(tree):
    _write(tree, "process", "orphan @BBL P2S", inherits="no_such_parent", instantiation="true")
    with pytest.raises(ProfileNotFound):
        load_profile("process", "orphan @BBL P2S", root=tree)


def test_inherits_cycle_is_rejected(tree):
    _write(tree, "process", "loop_a", inherits="loop_b")
    _write(tree, "process", "loop_b", inherits="loop_a")
    with pytest.raises(ValueError, match="cycle"):
        load_profile("process", "loop_a", root=tree)


def test_profile_path_layout(tree):
    assert profile_path("filament", "Bambu PLA Lite @base", root=tree) == (
        tree / "filament" / "Bambu PLA Lite @base.json"
    )


# --- list_profiles ----------------------------------------------------------


def test_list_profiles_p2s_04(tree):
    listing = list_profiles(printer="P2S", nozzle="0.4", root=tree)
    assert set(listing) == {"machines", "processes", "filaments"}

    assert _names(listing["machines"]) == ["Bambu Lab P2S 0.4 nozzle"]
    assert _names(listing["processes"]) == ["0.20mm Standard @BBL P2S"]
    assert _names(listing["filaments"]) == [
        "Bambu PETG HF @BBL P2S",
        "Bambu PLA Lite @BBL P2S 0.4 nozzle",
    ]

    names = _names(listing["processes"])
    assert "0.10mm Standard @BBL P2S 0.2 nozzle" not in names
    assert "0.20mm Template @BBL P2S" not in names
    assert "0.20mm Standard @BBL P2SC" not in names
    assert "0.20mm Standard @BBL X1C" not in names


def test_list_profiles_summaries(tree):
    listing = list_profiles(printer="P2S", nozzle="0.4", root=tree)

    assert listing["machines"][0] == {
        "name": "Bambu Lab P2S 0.4 nozzle",
        "nozzle_diameter": "0.4",
        "printable_height": "256",
        "default_bed_type": None,
    }
    assert listing["processes"][0] == {
        "name": "0.20mm Standard @BBL P2S",
        "description": "Standard profile",
        "layer_height": "0.2",
        "wall_loops": "2",
        "sparse_infill_density": "20%",
    }
    lite = listing["filaments"][1]
    assert lite == {
        "name": "Bambu PLA Lite @BBL P2S 0.4 nozzle",
        "filament_type": "PLA",
        "nozzle_temperature": "220",
        "nozzle_temperature_range_low": "190",
        "nozzle_temperature_range_high": "240",
        "textured_plate_temp": "55",
        "filament_density": "1.40",
        "filament_max_volumetric_speed": ["16", "40", "16"],
    }


def test_list_profiles_filament_filter(tree):
    listing = list_profiles(printer="P2S", nozzle="0.4", filament_contains="lite", root=tree)
    assert _names(listing["filaments"]) == ["Bambu PLA Lite @BBL P2S 0.4 nozzle"]


def test_list_profiles_other_nozzle(tree):
    listing = list_profiles(printer="P2S", nozzle="0.2", root=tree)
    assert _names(listing["machines"]) == ["Bambu Lab P2S 0.2 nozzle"]
    assert _names(listing["processes"]) == ["0.10mm Standard @BBL P2S 0.2 nozzle"]
    assert _names(listing["filaments"]) == ["Bambu PLA Lite @BBL P2S 0.2 nozzle"]


def test_list_profiles_skips_profiles_not_loadable_by_file_name(tree):
    # Bambu ships "Bambu Support For PA/PET @base" as "Bambu Support For PA PET @base.json".
    _write(tree, "filament", "Bambu Support For PA PET @base", instantiation="false")
    (tree / "filament" / "Bambu Support For PA PET @base.json").write_text(
        json.dumps({"name": "Bambu Support For PA/PET @base", "instantiation": "false"}),
        encoding="utf-8",
    )
    (tree / "filament" / "Bambu Support For PA PET @BBL P2S.json").write_text(
        json.dumps({
            "name": "Bambu Support For PA/PET @BBL P2S",
            "inherits": "Bambu Support For PA/PET @base",
            "instantiation": "true",
        }),
        encoding="utf-8",
    )
    _write(tree, "filament", "Broken Parent @BBL P2S", inherits="no_such_parent", instantiation="true")

    names = _names(list_profiles(printer="P2S", nozzle="0.4", root=tree)["filaments"])
    assert names == ["Bambu PETG HF @BBL P2S", "Bambu PLA Lite @BBL P2S 0.4 nozzle"]


def test_list_profiles_without_folder(tmp_path):
    with pytest.raises(ProfileNotFound):
        list_profiles(root=tmp_path / "missing")
