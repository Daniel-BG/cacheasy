app('address_width 32', echo=True)
app('line_size_width 4', echo=True)
app('create Apartado A', echo=True)
app('name Memory', echo=True)
app('memory', echo=True)
app('name Cache', echo=True)
app('set_width 4', echo=True)
app('way_width 0', echo=True)
app('policy FIFO', echo=True)
app('write_back True', echo=True)
app('write_allocate False', echo=True)
app('prefetch 0', echo=True)
app('cache', echo=True)
app('cost_hit 1', echo=True)
app('cost_miss 200', echo=True)
app('cost_through 200', echo=True)
app('reset_stats', echo=True)
for i in range(128):
    if (i > 7 and i < 64):
        app('read ' + str(0x200 + 4*i))
        app('write ' + str(4*i))
    else:
        app('read ' + str(0x200 + 4*i))
        app('read ' + str(0 + 4*i))
app('show_state stats', echo=True)