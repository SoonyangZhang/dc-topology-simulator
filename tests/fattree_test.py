import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import init
import unittest
from topology.fattree import *
import config as cfg
import collections
import random
from traffic.tenant import *

class Test_fattree(unittest.TestCase):
	def test_simplePath(self):
		cfg.k_FatTree = 4
		fattree = FatTree()
		fattree.generate()
		#fattree.printTopology()
		source = 'h_1_1_1'
		dest = 'h_3_2_2'
		firstShortestPathIDs = ['h_1_1_1','h_1_1_1+t_1_1', 't_1_1','t_1_1+a_1_1', 'a_1_1', 'a_1_1+c_1', 'c_1','a_3_1+c_1', 'a_3_1', 't_3_2+a_3_1','t_3_2','h_3_2_2+t_3_2', 'h_3_2_2']
		path = fattree.findPath(source,dest)
		pathIDs = []
		for component in path.getComponents():
			pathIDs.append(str(component.id))
		assert (pathIDs == firstShortestPathIDs)
		print("FatTree hop length: %.2f " % (path.getHopLength()))
		return True

	def test_print_topology(self):
		cfg.k_FatTree = 16
		fattree = FatTree()
		fattree.generate()
		fattree.printTopology()

	def test_hoplength(self):
		cfg.k_FatTree = 14 #686 server fattree => k=14
		fattree = FatTree()
		fattree.generate()
		hosts = fattree.getHosts()
		
		trials = 10 #10 trials as given
		iterations = 10
		distribution = dict()
		for iteration in range(iterations):
			pathlengths = []
			for trial in range(trials):
				randSource = random.choice(hosts.keys()) #pick a random source
				randDest = random.choice(hosts.keys()) #pick a random destination
				while(randSource == randDest):
					randDest = random.choice(hosts.keys())
				pathlengths.append((fattree.findPath(randSource, randDest)).getHopLength())
			pathlengths.sort()
			frequency = collections.Counter(pathlengths)
			for key in frequency.keys():
				if key in distribution.keys():
					distribution[key]+=frequency[key]
				else:
					distribution[key] = frequency[key]
		
		print("Distribution")			
		print(distribution.keys())
		print([float(x) / (trials * iterations) for x in distribution.values()])
		return True
	
	def test_disjointPath(self):
		cfg.k_FatTree = 20
		cfg.defaultBackupStrategy= BackupStrategy.TOR_TO_TOR
		fattree = FatTree()
		fattree.generate()
		source = 'h_1_1_1'
		dest = 'h_3_2_2'
		paths = []
		while True:
			path = fattree.findDisjointPath(source,dest,0,paths)
			if path is not None:
				paths.append(path)
				globals.simulatorLogger.info(path.__str__())
			else:
				break
		globals.simulatorLogger.info("Total disjoint paths found %s" % len(paths))
		return True
	
	def test_various_inputs(self):
		for k in range(4,100,2):
			cfg.k_FatTree = k
			fattree = FatTree()
			assert(fattree.generate())
			globals.simulatorLogger.info("k: " + str(k))
		return True

	def test_oktopus(self):
		allocated = 0
		notAllocated = 0
		for k in range(4,20,2):
			cfg.k_FatTree = k
			fattree = FatTree()
			assert(fattree.generate())
			globals.simulatorLogger.info("k: " + str(k))
			
			for tenant_number in range(10):
				vms = random.randrange((k * (k / 2) ** 2) / 2)
				globals.simulatorLogger.info(str(vms) + " VMs required by Tenant # " + str(tenant_number))
				bw = random.randrange(cfg.bandwidthPerLink / 10)
				if bw == 0:
					continue
				globals.simulatorLogger.info(str(bw) + " BW required by Tenant # " + str(tenant_number))
				tenant = Tenant("Testing Tenant", 1, 100, 100, 100)
				if fattree.oktopus(vms,bw, tenant):
					allocated += 1
				else:
					notAllocated += 1

		print "Allocated: " + str(allocated)
		print "Not Allocated: " + str(notAllocated)

	def test_localRouting(self):
		cfg.k_FatTree = 48
		fattree = FatTree()
		fattree.generate()
		#fattree.printTopology()
		source = 'h_1_1_1'
		dest = 'h_3_2_2'
		bandwidth = 10;
		path = fattree.findPath(source,dest,bandwidth)
		#fattree._reservePath(path,bandwidth,1,False)
		
		backupPaths = []
		components = path.getComponents()
		for compNO in  [3, 5, 7, 9]:
			remBW = components[compNO].getAvailableBWFromDevice(components[compNO-1])
			components[compNO].reserveBWFromDevice(remBW, components[compNO-1]) #reserve all to simulate a failure
			tempPath = fattree.findPath(components[compNO-1].getID(),dest,bandwidth)
			if tempPath is None:
				print ("Couldnt find a backup for"+str(components[compNO-1].getID())+" to %s failure"+ str(components[compNO].getID()))
				return False
			#fattree._reservePath(tempPath,bandwidth,compNO,False)
			backupPaths.append(tempPath)
			components[compNO].unReserveBWFromDevice(remBW,components[compNO-1])

		fattree._reservePath(path,bandwidth,0,False)
		
		#removeComponent
		
		i=0
		for backupPath in backupPaths:
			i=i+1
			print("FatTree hop length: %.2f " % (backupPath.getHopLength()+i))
			print backupPath
			linksToRemove = path.getOverlappingLinks(backupPath)
			backupPath.removeComponents(linksToRemove)
			fattree._reservePath(backupPath,bandwidth,i,False)

		
		#pathIDs = []
		#for component in path.getComponents():
		#	pathIDs.append(str(component.id))
		#assert (pathIDs == firstShortestPathIDs)
		#print("FatTree hop length: %.2f " % (path.getHopLength()))
		return True
	
	def test_bfs(self):
		cfg.k_FatTree = 6
		fattree = FatTree()
		fattree.generate()
		t = time.time()
		shortestOldCodePath = fattree.findDisjointPath('h_1_1_1', 'h_3_2_2', 100) # ['A', 'C', 'F']
		print "old time:" + str(time.time() - t)
		t = time.time()
		shortestNewCodePath = fattree.findPath('h_1_1_1', 'h_3_2_2', 100) # ['A', 'C', 'F']
		print "new time:" + str(time.time() - t)
		t = time.time()
		shortestPaths = fattree.shortest_paths('h_1_1_1', 'h_3_2_2') # ['A', 'C', 'F']
		print (time.time() - t)
		print shortestNewCodePath
		print shortestOldCodePath
		print len(shortestPaths)
		return True
	
if __name__ == '__main__':
	unittest.main()
