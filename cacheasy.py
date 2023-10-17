from enum import Enum
import numpy as np

rng = np.random.default_rng()

ReplacementPolicy = Enum('ReplacementPolicy', ['FIFO', 'LRU', 'MRU', 'RANDOM'])

class MainMemory:

    def __init__(self, name = "Main memory"):
        self.name = name
        

    def read_address(self, addr):
        print("[%d] Block read from main memory" % addr)
        return True

    def write_address(self, addr):
        print("[%d] Block written to main memory" % addr)
        return True



        

class CacheSet:

    def __init__(self, ways, replacement_policy):
        self.ways = ways
        self.lines = []
        self.replacement_policy = replacement_policy


    def contains(self, tag):
        for line in self.lines:
            if line.tag == tag:
                return True
                
        return False


    def read(self, tag):
        for (i, line) in enumerate(self.lines):
            if line.tag == tag:
                match self.replacement_policy:
                    case ReplacementPolicy.LRU | ReplacementPolicy.MRU:
                        elem = self.lines.pop(i)
                        self.lines.insert(0, elem)
                    case _:
                        pass
                        #doesnt matter for the rest
                return True
        return False

    #assumes the element is not in the set
    #and puts it if it fits. If it does not, it evicts a block and returns it
    def put(self, tag):
        if self.contains(tag):
            print("ERROR: adding existing element to cache set")
            exit()

        if len(self.lines) < self.ways:
            self.lines.insert(0, CacheLine(tag))
            return None
        else:
            #we are replacing!
            outgoing = None
            match self.replacement_policy:
                case ReplacementPolicy.RANDOM:
                    index = rng.randint(0, self.ways-1)
                    outgoing = self.lines[index]
                    self.lines[index] = CacheLine(tag)
                case ReplacementPolicy.FIFO | ReplacementPolicy.LRU:
                    outgoing = self.lines.pop()
                    self.lines.insert(0, CacheLine(tag))
                case ReplacementPolicy.MRU:
                    outgoing = self.lines.pop(0)
                    self.lines.push(CacheLine(tag))
                case _:
                    print("ERROR: using an unsupported policy")
                    exit()

            return outgoing
                
    #assume the element is already in the set!!
    def write(self, tag):
        for (i, line) in enumerate(self.lines):
            if line.tag == tag:
                match self.replacement_policy:
                    case ReplacementPolicy.LRU | ReplacementPolicy.MRU:
                        elem = self.lines.pop(i)
                        elem.dirty = 1
                        self.lines.insert(0, elem)
                    case _:
                        pass
                        #doesnt matter for the rest
                return True
        return False


class CacheLine:

    def __init__(self, tag):
        self.dirty = 0
        self.tag = tag

    def __str__(self):
        return "" + str(self.tag) + ":" + str(self.dirty)



class Cache:
    #TODO: Add victim caches, 

    def __init__(self, name, sets, ways, line_size, replacement_policy = ReplacementPolicy.LRU, write_back = True, write_allocate = True, load_from = None, store_to = None):
        self.replacement_policy = replacement_policy
        self.sets = sets #number of distinct sets of blocks. 1 set means fully associative
        self.ways = ways #number of blocks per set. 1 way means directly mapped
        self.line_size = line_size
        self.write_back = write_back
        self.write_allocate = write_allocate
        self.load_from = load_from
        self.store_to = store_to

        self.name = name

        #initialize set dictionary
        self.set_data = {}
        for i in range(sets):
            self.set_data[i] = CacheSet(self.ways, self.replacement_policy)

    def get_set(self, addr):
        block = addr // self.line_size
        set_num = block % self.sets
        return self.set_data[set_num]
    
    def get_tag(self, addr):
        block = addr // self.line_size
        tag_num = block // self.sets
        return tag_num


    def get_block(self, addr):
        candidate_set = self.get_set(addr)
        candidate_tag = self.get_tag(addr)
        if (candidate_set.contains(candidate_tag)):
            #success
            print("[%d] found in %s" % (addr, self.name))
        else:
            
            print("[%d] Tag %d not found in %s, asking %s" % (addr, candidate_tag, self.name, self.load_from.name))

            #TODO first check if the evicted tag gonna be dirtied and push it up, THEN pull down new data
            
            #TODO request also to victim cache if present
            #if data is not present, request it to higher levels of cache. If it can't get it, bad
            if not self.load_from.read_address(addr):
                return False

            outgoing = candidate_set.put(candidate_tag)
            if outgoing is not None and outgoing.dirty != 0:
                #TODO push up to higher memory to save (should always be present as it is coherent)
                outgoing_base_addr = (outgoing.tag * self.sets + candidate_tag) * self.line_size
                #TODO update block above
                print("[%d] Saving from %s to %s" % (outgoing_base_addr, self.name, self.store_to.name))
                self.store_to.write_address(outgoing_base_addr)

            print("[%d] Data transferred from %s to %s" % (addr, self.load_from.name, self.name))


    def read_address(self, addr):
        self.get_block(addr)
        self.get_set(addr).read(self.get_tag(addr))
        print("[%d] Data read at %s" % (addr, self.name))
        return True
        
    def write_address(self, addr):
        self.get_block(addr)
        self.get_set(addr).write(self.get_tag(addr))
        print("[%d] Data written at %s" % (addr, self.name))
        return True
        







def main():
    mem = MainMemory()
    
    cache = Cache("L1", 4, 2, 16, ReplacementPolicy.LRU, load_from = mem, store_to = mem)

    cache.read_address(0x2000)
    cache.read_address(0x2001)
    cache.read_address(0x2002)
    cache.write_address(0x2003)

    cache.write_address(0x3003)
    cache.write_address(0x4003)


main()