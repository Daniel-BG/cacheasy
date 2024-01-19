app('address_width 18', echo=True)
app('line_size_width 4', echo=True)
app('create Apartado A', echo=True)
app('name Memory', echo=True)
app('memory', echo=True)
app('name Cache', echo=True)
app('set_width 3', echo=True)
app('way_width 0', echo=True)
app('policy FIFO', echo=True)
app('write_back True', echo=True)
app('write_allocate True', echo=True)
app('cache', echo=True)
app('cost_access 2', echo=True)
app('cost_miss 150', echo=True)
app('reset_costs', echo=True)
dir_a = 0x10000
dir_b = dir_a + 16*16*4
dir_c = dir_b + 32*4
for i in range(16):
    app('read ' + str(dir_b + 4), echo=True)
    app('read ' + str(dir_a + 4*i), echo=True)
    app('write ' + str(dir_c + 4*i), echo=True)
app('show_state stats', echo=True)
app('show_costs', echo=True)

#int A [16][16];
#int B [32];
#int C [16][16];
#for ( i =0; i < 16; i ++):
#    C [0][ i ] = A [0][ i ] + B [4];