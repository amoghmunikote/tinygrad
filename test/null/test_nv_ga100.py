import unittest, unittest.mock
from tinygrad.runtime.support.nv.nvdev import CHIP_ARCH_NAMES, CHIP_FW_NAMES, CHIP_FW_OVERRIDES

def resolve_fw_name(architecture:int, implementation:int) -> str:
  chip_name = CHIP_ARCH_NAMES[architecture] + f"{implementation:02d}"
  return CHIP_FW_OVERRIDES.get(chip_name, CHIP_FW_NAMES[chip_name[:3]])

class TestNVGA100ChipDetection(unittest.TestCase):
  def test_ga100_resolves_to_its_own_fw_name(self):
    self.assertEqual(resolve_fw_name(architecture=0x17, implementation=0x00), "ga100")

  def test_ga102_still_resolves_to_ga102(self):
    self.assertEqual(resolve_fw_name(architecture=0x17, implementation=0x02), "ga102")

  def test_other_chips_unaffected_by_the_override(self):
    self.assertEqual(resolve_fw_name(architecture=0x16, implementation=0x02), "tu102")
    self.assertEqual(resolve_fw_name(architecture=0x19, implementation=0x02), "ad102")
    self.assertEqual(resolve_fw_name(architecture=0x1b, implementation=0x02), "gb202")

class TestNVGA100PCIAllowlist(unittest.TestCase):
  # confirmed against pci-ids.ucw.cz
  GA100_DEVICE_IDS = [0x20B0, 0x20B1, 0x20B2, 0x20B5, 0x20B7, 0x20C2, 0x20F1, 0x2082]

  def test_ga100_device_ids_fall_in_the_0x2000_bucket(self):
    for dev_id in self.GA100_DEVICE_IDS:
      self.assertEqual(dev_id & 0xff00, 0x2000, f"{dev_id:#x} not in the 0x2000 bucket")

  def test_pciiface_allowlist_includes_the_0x2000_bucket(self):
    # read the source directly rather than importing ops_nv.py, which asserts POSIX-only at import time
    import pathlib
    src = (pathlib.Path(__file__).parents[2] / "tinygrad/runtime/ops_nv.py").read_text()
    assert "0x2000" in src.split("class PCIIface")[1].split("class ", 1)[0], \
      "PCIIface allowlist is missing the GA100 (0x2000) device-ID bucket"

class TestSystemPaddrsRounding(unittest.TestCase):
  def test_non_page_aligned_size_reads_a_full_page_of_pagemap_entries(self):
    from tinygrad.runtime.support.system import System
    fake_pagemap = unittest.mock.MagicMock()
    fake_pagemap.read.return_value = (0x8000000000000000).to_bytes(8, 'little') # one present-page pagemap entry
    with unittest.mock.patch.object(type(System), "pagemap", fake_pagemap):
      System.system_paddrs(vaddr=0, size=72) # sub-page-size request (GSP_ARGUMENTS_CACHED is 72 bytes)
    # ceildiv(72, PAGESIZE) * 8 == 8 (one pagemap entry), not the old buggy floor-div result of 0
    fake_pagemap.read.assert_called_once_with(8, binary=True)

if __name__ == '__main__':
  unittest.main()
