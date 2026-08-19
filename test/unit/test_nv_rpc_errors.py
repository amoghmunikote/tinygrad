import unittest, itertools, types
from tinygrad.runtime.autogen import nv, nv_570 as nv_gpu
from tinygrad.runtime.support.nv.ip import NV_GSP

class StatQ:
  def __init__(self, resp:bytes): self.resp = resp
  def wait_resp(self, cmd:int): return self.resp

class TestNVRpcErrors(unittest.TestCase):
  def _gsp(self, resp:bytes) -> NV_GSP:
    gsp = NV_GSP.__new__(NV_GSP)
    gsp.nvdev = types.SimpleNamespace(chip_name="GA102")
    gsp.priv_root, gsp.handle_gen = 0xc1e00004, itertools.count(1)
    gsp.gpfifo_class, gsp.compute_class = -1, -1 # avoid the gpfifo/compute-specific promote_ctx branches
    gsp.cmd_q = types.SimpleNamespace(send_rpc=lambda func, msg: None)
    gsp.stat_q = StatQ(resp)
    return gsp

  def test_rm_alloc_raises_on_error_status(self):
    resp = bytes(nv.rpc_gsp_rm_alloc_v(status=nv_gpu.NV_ERR_INVALID_ARGUMENT))
    with self.assertRaisesRegex(RuntimeError, "NV_ERR_INVALID_ARGUMENT"):
      self._gsp(resp).rpc_rm_alloc(hParent=0, hClass=0x1234, params=None)

  def test_rm_alloc_returns_object_on_success(self):
    resp = bytes(nv.rpc_gsp_rm_alloc_v(status=nv_gpu.NV_OK))
    self.assertIsInstance(self._gsp(resp).rpc_rm_alloc(hParent=0, hClass=0x1234, params=None), int)

  def test_rm_control_raises_on_error_status(self):
    resp = bytes(nv.rpc_gsp_rm_control_v(status=nv_gpu.NV_ERR_NOT_SUPPORTED))
    with self.assertRaisesRegex(RuntimeError, "NV_ERR_NOT_SUPPORTED"):
      self._gsp(resp).rpc_rm_control(hObject=1, cmd=0x1234, params=None)

  def test_rm_control_returns_none_params_on_success(self):
    resp = bytes(nv.rpc_gsp_rm_control_v(status=nv_gpu.NV_OK))
    self.assertIsNone(self._gsp(resp).rpc_rm_control(hObject=1, cmd=0x1234, params=None))

if __name__ == "__main__":
  unittest.main()
