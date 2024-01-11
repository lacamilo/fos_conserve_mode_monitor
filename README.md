<p align="center">Conserve mode monitor tool</p>

The conserve_mode_monitor intends to provide a seamless way to collect in depth debug output when the memory is under presure. 
It's a common mistake to collect these output when the conserve mode is gone and after it has happened in the past. The output will only reveal a normal memory consumption. 

The conserve_mode_monitor tool will collect the output from "get system performance status" and "diag sys top-mem 16" and parse it. 
The tool will monitor from "get system performance status" if the threshold is crossed. Once the overall used memory goes beyond 79%, it will check the second output. 
"diag sys top-mem 16" will provide individual memory usage from each process. Once the treshold of 500Mb is crossed, the tool will collect extenside debug output from that process or feature specifically. 
After collecting the debug output, the tool can "kill" the PID associated with the process if that option is enabled (disabled by default). What can offer some workaround for the time being in some cases.

------------ High memory found ipsengine ------------<br>
diag sys process dump {pid}<br>
diag sys process pstack {pid}<br>
fnsysctl du /dev/shm<br>
sleep for 5 seconds <br>
diag sys process pstack {pid}<br>
fnsysctl du /dev/shm<br>
diag ips memory status<br>
diag ips session status<br>
diag test application ipsmonitor 24<br>

------------ High memory found wad ------------<br>
diag sys process dump {pid}<br>
diag sys process pstack {pid}<br>
fnsysctl du /dev/shm<br>
sleep for 5 seconds <br>
diag wad stats worker.sysmem<br>
diag sys process pstack {pid}<br>
fnsysctl du /dev/shm<br>
diag wad memory overused<br>
