app('address_width 16', echo=True)
app('line_size_width 4', echo=True)
app('create Apartado A', echo=True)
app('name Memory', echo=True)
app('memory', echo=True)
app('name Cache', echo=True)
app('set_width 2', echo=True)
app('way_width 0', echo=True)
app('policy LRU', echo=True)
app('write_back True', echo=True)
app('write_allocate True', echo=True)
app('cache', echo=True)

dir_v = 0x0
dir_mask = dir_v + 16*4

for i in range(12):
    for j in range(4):
        app('read ' + str(dir_v + i*4), echo=False)
        app('read ' + str(dir_mask + j*4), echo=False)
    app('write ' + str(dir_v + i*4), echo=False)


app('show_state stats', echo=True)