"""print_mcp.profiles: reading Bambu Studio profiles and their `inherits` chains."""
from __future__ import annotations

import json
import os

import pytest

from print_mcp.profiles import (
    ProfileNotFound,
    flatten_profile,
    list_profiles,
    load_profile,
    profile_path,
    raw_profile,
)


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


# --- include ----------------------------------------------------------------


@pytest.fixture
def machine_with_templates(tree):
    """A machine like the P2S: generic G-code in the parent, P2S G-code in templates."""
    _write(tree, "machine", "fdm_bbl_common", instantiation="false",
           machine_start_gcode="G28 ; generic", machine_end_gcode="M84 ; generic",
           retraction_length=["0.8"], printable_height="250")
    _write(tree, "machine", "P2S template machine_start_gcode", instantiation="false",
           machine_start_gcode=";=== P2S start ===")
    _write(tree, "machine", "P2S template machine_end_gcode", instantiation="false",
           machine_end_gcode=";=== P2S end ===", retraction_length=["0.6"])
    _write(tree, "machine", "Bambu Lab P2S 0.4 nozzle", inherits="fdm_bbl_common",
           instantiation="true", setting_id="GM049", printable_height="256",
           retraction_length=["0.5"],
           include=["P2S template machine_start_gcode", "P2S template machine_end_gcode"])
    return tree


def test_include_templates_override_parents_and_leaf_overrides_templates(machine_with_templates):
    profile = load_profile("machine", "Bambu Lab P2S 0.4 nozzle", root=machine_with_templates)
    assert profile["machine_start_gcode"] == ";=== P2S start ==="
    assert profile["machine_end_gcode"] == ";=== P2S end ==="
    assert profile["retraction_length"] == ["0.5"]
    assert profile["printable_height"] == "256"
    # Template identity keys never leak into the including profile.
    assert profile["name"] == "Bambu Lab P2S 0.4 nozzle"
    assert profile["instantiation"] == "true"
    assert profile["setting_id"] == "GM049"


def test_template_with_its_own_links_is_rejected(machine_with_templates):
    _write(machine_with_templates, "machine", "nested template", inherits="fdm_bbl_common")
    _write(machine_with_templates, "machine", "nested user", instantiation="true",
           include=["nested template"])
    with pytest.raises(ValueError, match="template"):
        load_profile("machine", "nested user", root=machine_with_templates)


def test_missing_template_raises_profile_not_found(tree):
    _write(tree, "machine", "lonely", instantiation="true", include=["no such template"])
    with pytest.raises(ProfileNotFound):
        load_profile("machine", "lonely", root=tree)


def test_flatten_profile_is_self_contained(machine_with_templates):
    flat = flatten_profile("machine", "Bambu Lab P2S 0.4 nozzle", root=machine_with_templates)
    assert "inherits" not in flat
    assert "include" not in flat
    assert flat["name"] == "Bambu Lab P2S 0.4 nozzle"
    assert flat["type"] == "machine"
    assert flat["setting_id"] == "GM049"
    assert flat["machine_start_gcode"] == ";=== P2S start ==="
    assert flat["retraction_length"] == ["0.5"]


# --- vendor index -----------------------------------------------------------


@pytest.fixture
def indexed_tree(tree):
    """`BBL.json` next to the BBL folder, like Bambu Studio's resources/profiles/BBL.json."""
    support_base = "Bambu Support For PA/PET @base"
    support_p2s = "Bambu Support For PA/PET @BBL P2S"
    (tree / "filament" / "Bambu Support For PA PET @base.json").write_text(
        json.dumps({"type": "filament", "name": support_base, "instantiation": "false",
                    "filament_density": ["1.20"], "filament_type": ["Support"]}),
        encoding="utf-8",
    )
    (tree / "filament" / "Bambu Support For PA PET @BBL P2S.json").write_text(
        json.dumps({"type": "filament", "name": support_p2s, "inherits": support_base,
                    "instantiation": "true", "nozzle_temperature": ["250"]}),
        encoding="utf-8",
    )
    (tree / "filament" / "SUNLU").mkdir()
    (tree / "filament" / "SUNLU" / "SUNLU PLA @base.json").write_text(
        json.dumps({"type": "filament", "name": "SUNLU PLA @base", "instantiation": "false"}),
        encoding="utf-8",
    )

    def entries(kind):
        return [
            {"name": path.stem, "sub_path": f"{kind}/{path.name}"}
            for path in sorted((tree / kind).glob("*.json"))
            if not path.stem.startswith("Bambu Support")
        ]

    index = {
        "name": "Bambulab",
        "machine_list": entries("machine"),
        "process_list": entries("process"),
        "filament_list": entries("filament") + [
            {"name": support_base, "sub_path": "filament/Bambu Support For PA PET @base.json"},
            {"name": support_p2s, "sub_path": "filament/Bambu Support For PA PET @BBL P2S.json"},
            {"name": "SUNLU PLA @base", "sub_path": "filament/SUNLU/SUNLU PLA @base.json"},
            {"name": "Escape @BBL P2S", "sub_path": "filament/../../escape.json"},
            {"name": "Absolute @BBL P2S", "sub_path": "C:/escape.json"},
        ],
    }
    (tree.parent / "BBL.json").write_text(json.dumps(index), encoding="utf-8")
    return tree


def test_index_maps_names_with_slash(indexed_tree):
    name = "Bambu Support For PA/PET @BBL P2S"
    assert profile_path("filament", name, root=indexed_tree) == (
        indexed_tree / "filament" / "Bambu Support For PA PET @BBL P2S.json"
    )
    profile = load_profile("filament", name, root=indexed_tree)
    assert profile["name"] == name
    assert profile["filament_density"] == ["1.20"]
    assert profile["nozzle_temperature"] == ["250"]


def test_index_reaches_subfolders(indexed_tree):
    assert load_profile("filament", "SUNLU PLA @base", root=indexed_tree)["name"] == "SUNLU PLA @base"


@pytest.mark.parametrize("name", ["a/b", "..\\x", "a;b", "C:x", "Escape @BBL P2S/.."])
def test_index_does_not_open_bad_names(indexed_tree, name):
    with pytest.raises(ValueError):
        load_profile("filament", name, root=indexed_tree)


def test_index_entries_outside_the_kind_folder_are_ignored(indexed_tree):
    for name in ("Escape @BBL P2S", "Absolute @BBL P2S"):
        assert profile_path("filament", name, root=indexed_tree) == (
            indexed_tree / "filament" / f"{name}.json"
        )
        with pytest.raises(ProfileNotFound):
            load_profile("filament", name, root=indexed_tree)


def _write_index(tree, kind, entries):
    lists = {f"{other}_list": [] for other in ("machine", "process", "filament")}
    lists[f"{kind}_list"] = entries
    (tree.parent / "BBL.json").write_text(json.dumps(lists), encoding="utf-8")


@pytest.mark.parametrize("sub_path", ["machine/C:/Windows/x.json", "machine/D:/x.json"])
def test_index_entries_with_a_drive_are_ignored(tree, sub_path):
    # On Windows, joining "C:" or "D:" onto the profile folder jumps to another drive.
    _write_index(tree, "machine", [{"name": "Drive @BBL P2S", "sub_path": sub_path}])
    assert profile_path("machine", "Drive @BBL P2S", root=tree) == (
        tree / "machine" / "Drive @BBL P2S.json"
    )
    with pytest.raises(ProfileNotFound):
        load_profile("machine", "Drive @BBL P2S", root=tree)


def test_index_entry_through_a_link_outside_is_rejected(tree, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside_profiles")
    (outside / "x.json").write_text(json.dumps({"name": "Linked"}), encoding="utf-8")
    link = tree / "machine" / "linked"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        try:
            import _winapi

            _winapi.CreateJunction(str(outside), str(link))
        except (ImportError, AttributeError, OSError):
            pytest.skip("cannot create a directory link on this machine")
    _write_index(tree, "machine", [{"name": "Linked", "sub_path": "machine/linked/x.json"}])
    with pytest.raises(ValueError, match="outside"):
        load_profile("machine", "Linked", root=tree)


def test_raw_profile_is_the_file_itself(tree):
    raw = raw_profile("process", "0.20mm Standard @BBL P2S", root=tree)
    assert raw["inherits"] == "fdm_process_common"
    assert "layer_height" not in raw
    raw["description"] = "changed"
    assert raw_profile("process", "0.20mm Standard @BBL P2S", root=tree)["description"] == "Standard profile"


def test_list_profiles_with_index_includes_slash_names(indexed_tree):
    names = _names(list_profiles(printer="P2S", nozzle="0.4", root=indexed_tree)["filaments"])
    assert names == [
        "Bambu PETG HF @BBL P2S",
        "Bambu PLA Lite @BBL P2S 0.4 nozzle",
        "Bambu Support For PA/PET @BBL P2S",
    ]


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
    # Bambu ships "Bambu Support For PA/PET @base" as "Bambu Support For PA PET @base.json";
    # without a vendor index that name cannot be found, so its children are left out.
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
