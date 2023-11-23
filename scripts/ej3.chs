address_width 22
line_size_width 9
create Apartado A
name Memory
memory
name Cache
set_width 2
way_width 1
policy FIFO
write_back True
write_allocate True
prefetch 0
cache
name Victim
set_width 0
way_width 1
victim
read 0x3ffe00
read 0x150000

read 0x004000
read 0x334000
read 0x1e4200
read 0x14ba00
read 0x334400
read 0x2ffc00
read 0x14be00
read 0x100600

show_state 
reset_statistics

read 0x334500
read 0x14bf00
read 0x150084
read 0x004021
read 0x0540AB
read 0x0041F1
show_state