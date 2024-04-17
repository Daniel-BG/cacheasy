address_width 12
line_size_width 7
create Ejemplo
name Memory
memory
name Cache
#set_width 3
#way_width 0
set_width 0
way_width 3
#set_width 2
#way_width 1
policy LRU
write_back True
write_allocate True
cache
#cost_access 10
#cost_miss 100
#reset_costs
show_state
read 0x100
read 0x500
read 0x900
read 0x500
read 0x900
read 0x500
read 0x900
read 0x500
read 0x900
read 0x500
read 0x900
read 0x500
read 0x100
show_state
show_costs