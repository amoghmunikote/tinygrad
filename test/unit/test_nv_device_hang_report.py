import unittest, types
from tinygrad.runtime.autogen import nv_570 as nv_gpu
from tinygrad.runtime.ops_nv import NVDevice

class TestNVDeviceHangReport(unittest.TestCase):
  def _dev(self, rm_control) -> NVDevice:
    dev = NVDevice.__new__(NVDevice)
    dev.iface, dev.debugger, dev.debug_channel = types.SimpleNamespace(rm_control=rm_control), 1, 2
    return dev

  def test_report_survives_debugger_rpc_failure(self):
    def rm_control(*a, **k): raise RuntimeError("rm_control 0x83de0100 on 0x5 returned 5: NV_ERR_INVALID_STATE")
    with self.assertRaisesRegex(RuntimeError, "graphics debugger state unavailable"):
      self._dev(rm_control).on_device_hang()

  def test_report_is_never_empty(self):
    def rm_control(*a, **k): return nv_gpu.NV83DE_CTRL_DEBUG_READ_ALL_SM_ERROR_STATES_PARAMS()
    with self.assertRaisesRegex(RuntimeError, "no fault state reported"):
      self._dev(rm_control).on_device_hang()

  def test_report_includes_mmu_fault(self):
    def rm_control(hObject, cmd, params, **k):
      if cmd == nv_gpu.NV83DE_CTRL_CMD_DEBUG_READ_ALL_SM_ERROR_STATES:
        sm = nv_gpu.NV83DE_CTRL_DEBUG_READ_ALL_SM_ERROR_STATES_PARAMS()
        sm.mmuFault.valid = 1
        return sm
      mmu = nv_gpu.NV83DE_CTRL_DEBUG_READ_MMU_FAULT_INFO_PARAMS(count=1)
      mmu.mmuFaultInfoList[0].faultAddress, mmu.mmuFaultInfoList[0].faultType, mmu.mmuFaultInfoList[0].accessType = 0x1000, 0, 0
      return mmu
    with self.assertRaisesRegex(RuntimeError, "MMU fault"):
      self._dev(rm_control).on_device_hang()

if __name__ == "__main__":
  unittest.main()
