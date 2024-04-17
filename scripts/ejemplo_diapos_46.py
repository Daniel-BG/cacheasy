app('address_width 16', echo=True)
app('line_size_width 4', echo=True)
app('create Apartado A', echo=True)
app('name Memory', echo=True)
app('memory', echo=True)
app('name Cache', echo=True)
app('set_width 8', echo=True)
app('way_width 0', echo=True)
app('policy LRU', echo=True)
app('write_back True', echo=True)
app('write_allocate True', echo=True)
app('cache', echo=True)

dir_a = 0x0

for i in range(128):
    for j in range(128):
        app('read ' + str(dir_a + i*128*4 + j*4), echo=False)
        

app('show_state stats', echo=True)