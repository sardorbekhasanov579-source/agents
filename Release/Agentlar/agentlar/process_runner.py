"""Windows command trampoline: join a kill-on-close job before spawning children.

This is lifecycle containment, NOT a security sandbox. The job handle deliberately
remains open until this process exits, at which point remaining children are killed.
"""
import ctypes
import json
import os
import subprocess
import sys

_job = None

def windows_job():
    from ctypes import wintypes as w
    class Basic(ctypes.Structure):
        _fields_=[('PerProcessUserTimeLimit',ctypes.c_longlong),('PerJobUserTimeLimit',ctypes.c_longlong),
                  ('LimitFlags',w.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),
                  ('ActiveProcessLimit',w.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]
    class IO(ctypes.Structure):
        _fields_=[(n,ctypes.c_ulonglong) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]
    class Extended(ctypes.Structure):
        _fields_=[('BasicLimitInformation',Basic),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR]; kernel.CreateJobObjectW.restype=w.HANDLE
    kernel.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]; kernel.SetInformationJobObject.restype=w.BOOL
    kernel.GetCurrentProcess.argtypes=[]; kernel.GetCurrentProcess.restype=w.HANDLE
    kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]; kernel.AssignProcessToJobObject.restype=w.BOOL
    handle=kernel.CreateJobObjectW(None,None)
    if not handle: raise ctypes.WinError(ctypes.get_last_error())
    info=Extended(); info.BasicLimitInformation.LimitFlags=0x2000  # KILL_ON_JOB_CLOSE
    if not kernel.SetInformationJobObject(handle,9,ctypes.byref(info),ctypes.sizeof(info)): raise ctypes.WinError(ctypes.get_last_error())
    if not kernel.AssignProcessToJobObject(handle,kernel.GetCurrentProcess()): raise ctypes.WinError(ctypes.get_last_error())
    return handle

if __name__=='__main__':
    try:
        if os.name=='nt': _job=windows_job()
        argv=json.loads(sys.argv[1])
        result=subprocess.run(argv,stdin=subprocess.DEVNULL,shell=False)
        sys.stdout.flush(); sys.stderr.flush()
        sys.exit(result.returncode)
    except Exception as exc:
        print('Buyruq ishga tushmadi: '+str(exc),file=sys.stderr); sys.exit(1)
