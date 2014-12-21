from topology import *
import config as cfg
import globals as globals

#import logging

class FatTree(Tree):
	def __init__(self):
		Tree.__init__(self, TopologyType.FATTREE)
		self.k = cfg.k_FatTree
		self.bw = cfg.bandwidthPerLink
		self.VMsInHost = cfg.VMsInHost
		self.VMsInRack = 0
		self.VMsInPod = 0
		self.VMsInDC = 0

		self.availabilityUnderHosts = dict()
		self.availabilityUnderRacks = dict()
		self.availabilityUnderPods = dict()
		self.availabilityUnderDC = (0, self.bw)

# over-loaded __str__() for print functionality
	def __str__(self):
		printString =  "=========================="
		printString += "\nTopology Information"
		printString += "\n--------------------------"
		printString += "\nTopology:    " + str(self.topologyType)
		printString += "\nk:           " + str(self.k)
		printString += "\nDevices:     " + str(len(self.devices))
		printString += "\nLinks:       " + str(len(self.links))
		printString += "\nAllocations: " + str(len(self._traffics))
		printString += "\nFree VMs:    " + str(self.availabilityUnderDC[0])
		printString += "\n=========================="
		return printString


	def generate(self):
		try:
			# *** TAKE INPUT FROM USER. ***
			if(cfg.overrideDefaults):
				self.k = int(raw_input("Enter value of k: "))
			assert (self.k > 0) and (self.k%2 == 0)
		except:
			globals.simulatorLogger.error("Invalid inputs! Please try again. Exiting...")
			return None

		globals.simulatorLogger.info("Generating " + str(self.k) + "-ary FatTree topology")
		self.VMsInRack = self.VMsInHost * self.k / 2
		self.VMsInPod = self.VMsInRack * self.k / 2
		self.VMsInDC = self.VMsInPod * self.k
		# initialize lists
		cores = []
		aggrs = []
		tors = []
		hosts = []
		# add (k/2)^2 cores
		for c in range(self.k*self.k/4):
			coreName = "c_" + str(c+1)
			core = Device(coreName, "core")
			cores.append(core)
		# add pods with k/2 aggrs and k/2 tors, with k/2 hosts per tor
		for pod in range(self.k):
			for sw in range(self.k/2):
				aggrName = "a_" + str(pod+1) + "_" + str(sw+1)
				torName = "t_" + str(pod+1) + "_" + str(sw+1)
				aggr = Device(aggrName, "aggr")
				tor = Device(torName, "tor")
				for h in range(self.k/2):
					hostName = "h_" + str(pod+1) + "_" + str(sw+1) + "_" + str(h+1)
					host = Device(hostName, "host", True)
					linkName = host.getID()+"+"+tor.getID()
					hostLink = Link(linkName, "torLink", self.bw, host, tor)
					host.addLink(hostLink)
					tor.addLink(hostLink)
					hosts.append(host)
					self.links[linkName] = hostLink
				aggrs.append(aggr)
				tors.append(tor)
		# connecting tor and aggr switches
		for i in range(self.k):
			for j in range(self.k/2):
				for l in range(self.k/2):
					name = tors[self.k/2*i+j].getID()+"+"+aggrs[self.k/2*i+l].getID()
					torLink = Link(name, "aggrLink", self.bw, tors[self.k/2*i+j], aggrs[self.k/2*i+l])
					tors[self.k/2*i+j].addLink(torLink)
					aggrs[self.k/2*i+l].addLink(torLink)
					self.links[name] = torLink
		# connecting aggr and core switches
		for podNumber in range(self.k):
			for aggregatorNumberInPod in range(self.k/2):
				for coreNumber in range(self.k/2):
					name = aggrs[podNumber*(self.k/2)+aggregatorNumberInPod].getID()+"+"+cores[aggregatorNumberInPod*(self.k/2)+coreNumber].getID()
					coreLink = Link(name, "coreLink", self.bw, aggrs[podNumber*(self.k/2)+aggregatorNumberInPod], cores[aggregatorNumberInPod*(self.k/2)+coreNumber])
					aggrs[podNumber*(self.k/2)+aggregatorNumberInPod].addLink(coreLink)
					cores[aggregatorNumberInPod*(self.k/2)+coreNumber].addLink(coreLink)
					self.links[name] = coreLink			
		for host in hosts:
			_id = host.getID()
			self.devices[_id] = host
			self.availabilityUnderHosts[_id] = (self.VMsInHost, self.bw)
		for tor in tors:
			self.devices[tor.getID()] = tor
			self.availabilityUnderRacks[_id] = (self.VMsInRack, self.bw)
		for aggr in aggrs:
			self.devices[aggr.getID()] = aggr
			self.availabilityUnderPods[_id] = (self.VMsInPod, self.bw)
		for core in cores:
			self.devices[core.getID()] = core
		self.availabilityUnderDC = (self.VMsInDC, self.bw)
		return True


	def getAllHosts(self):
		return [_device for _device in self.devices.values() if _device.getLabel() == "host"]

	def getAllTors(self):
		return [_device for _device in self.devices.values() if _device.getLabel() == "tor"]

	def getAllAggrs(self):
		return [_device for _device in self.devices.values() if _device.getLabel() == "aggr"]

	def getAllCores(self):
		return [_device for _device in self.devices.values() if _device.getLabel() == "core"]


	#def findPath(self, start, end, _bw):
	#	_start = self.devices[start] # start node
	#	_end = self.devices[end] # end node

	#	startSW = _start.getLink().getOtherDevice(_start)
	#	endSW = _end.getLink().getOtherDevice(_end)
	#	startPod = _start.getID().split("_")[1]
	#	endPod = _end.getID().split("_")[1]

	#	paths = []
	#	if startSW == endSW:
	#		pass
	#	elif startPod == endPod:
	#		paths = self.getIntraPodPaths(_start, _end, _bw)
	#	else:
	#		paths = self.getInterPodPaths(_start, _end, _bw)

	#	if len(paths) == 0:
	#		globals.simulatorLogger.warning("No valid path found.")
	#		return None
	#	primaryPath = random.choice(list(paths))
	#	return primaryPath
		
		# ???
		# The "paths" variable is local, so there is no need to delete from it. Is there?
		# ind = paths.index(primaryPath)
		# del paths[ind]
		# ???

		# ???
		# This should not be happening in this function, it should only return the path. Right?
		# flow = Flow(_id, _label, _time, _active, _bw, _start, _end)
		# flow.addPath(primaryPath)
		# return flow
		# ???

	def findDisjointPath(self, start, end, _bw, curPaths=[]):
		if curPaths is None:
			return None
		
		_start = self.devices[start] # start node
		_end = self.devices[end] # end node

		startSW = _start.getLink().getOtherDevice(_start)
		endSW = _end.getLink().getOtherDevice(_end)
		startPod = _start.getID().split("_")[1]
		endPod = _end.getID().split("_")[1]

		paths = []
		if startSW == endSW:
			# no disjoint paths if hosts under same tor
			# TODO: may need exception if tor to tor paths needed
			# pass
			return None
		
		if startPod == endPod:
			paths = self.getIntraPodPaths(_start, _end, _bw)
		else:
			paths = self.getInterPodPaths(_start, _end, _bw)

		validDisjointPaths = []
		isValid = True
		for path in paths:
			isValid = True
			for component in path.getComponents():
				if not isValid:
					break
				for curPath in curPaths:
					if component in curPath.getComponents():
						if isinstance(component, Link):
							if component.getLabel() == "torLink":
								continue
						elif isinstance(component, Device):
							if component.getLabel() == "tor":
								continue
						isValid = False
						break
			if isValid:
				validDisjointPaths.append(path)

		# no disjoint path found
		if len(validDisjointPaths) == 0:
			return None
		
		disjointPath = random.choice(list(validDisjointPaths))
		return disjointPath

	def getIntraPodPaths(self, _start, _end, _bw):
		paths = []
		startSW = _start.getLink().getOtherDevice(_start)
		endSW = _end.getLink().getOtherDevice(_end)

		for aggrLink in startSW.getAllLinks():
			aggrSW = aggrLink.getOtherDevice(startSW)
			if not aggrSW.getStatus() == Status.AVAILABLE:
				continue
			aggrBW = aggrLink.getAvailableBW(startSW)

			if aggrSW.getID().split("_")[0] == "a" and aggrBW >= _bw:
				for torLink in aggrSW.getAllLinks():
					torSW = torLink.getOtherDevice(aggrSW)
					if torSW.getStatus() is not Status.AVAILABLE:
						continue
					torBW = torLink.getAvailableBW(aggrSW)

					if torSW == endSW and torSW.getID().split("_")[0] == "t" and torBW >= _bw:
						path = Path()
						path.append(_start)
						path.append(_start.getLink())
						path.append(startSW)
						path.append(aggrLink)
						path.append(aggrSW)
						path.append(torLink)
						path.append(endSW)
						path.append(_end.getLink())
						path.append(_end)
						paths.append( path )
		return paths

	def getInterPodPaths(self, _start, _end, _bw):
		paths = []
		startSW = _start.getLink().getOtherDevice(_start)
		startPod = _start.getID().split("_")[1]
		endSW = _end.getLink().getOtherDevice(_end)
		endPod = _end.getID().split("_")[1]

		for aggrLink in startSW.getAllLinks():
			aggrSW = aggrLink.getOtherDevice(startSW)
			if not aggrSW.getStatus() == Status.AVAILABLE:
				continue
			aggrBW = aggrLink.getAvailableBW(startSW)

			if aggrSW.getID().split("_")[0] == "a" and aggrBW >= _bw:
				for coreLink in aggrSW.getAllLinks():
					coreSW = coreLink.getOtherDevice(aggrSW)
					if coreSW.getStatus() is not Status.AVAILABLE:
						continue
					coreBW = coreLink.getAvailableBW(aggrSW)

					if coreSW.getID().split("_")[0] == "c" and coreBW >= _bw:
						for aggLink in coreSW.getAllLinks():
							aggSW = aggLink.getOtherDevice(coreSW)
							if aggSW.getStatus() is not Status.AVAILABLE:
								continue
							aggBW = aggLink.getAvailableBW(coreSW)

							if aggSW.getID().split("_")[1] == endPod and aggSW.getID().split("_")[0] == "a" and aggBW >= _bw:
								for torLink in aggSW.getAllLinks():
									torSW = torLink.getOtherDevice(aggSW)
									if torSW.getStatus() is not Status.AVAILABLE:
										continue
									torBW = torLink.getAvailableBW(aggSW)

									if torSW == endSW and torSW.getID().split("_")[0] == "t" and torBW >= _bw:
										path = Path()
										path.append(_start)
										path.append(_start.getLink())
										path.append(startSW)
										path.append(aggrLink)
										path.append(aggrSW)
										path.append(coreLink)
										path.append(coreSW)
										path.append(aggLink)
										path.append(aggSW)
										path.append(torLink)
										path.append(endSW)
										path.append(_end.getLink())
										path.append(_end)
										paths.append( path )
		return paths


	# TODO: Need to check if this function is needed or not!
	# def allocate(self, id, vms, bw):
	# 	if vms < self.VMsInHost:
	# 		for _id, _avail in self.availabilityUnderHosts.iteritems():
	# 			if _avail[0] >= vms and _avail[1] >= bw:
	# 				if self.alloc(self.devices[_id], vms, bw):
	# 					return True

	# 	if vms < self.VMsInRack:
	# 		for _id, _avail in self.availabilityUnderRacks.iteritems():
	# 			if _avail[0] >= vms and _avail[1] >= bw:
	# 				if self.alloc(self.devices[_id], vms, bw):
	# 					return True

	# 	if vms < self.VMsInPod:
	# 		for _id, _avail in self.availabilityUnderPods.iteritems():
	# 			if _avail[0] >= vms and _avail[1] >= bw:
	# 				if self.alloc(self.devices[_id], vms, bw):
	# 					return True

	# 	if vms < self.VMsInDC:
	# 		availVMs = self.availabilityUnderDC[0]
	# 		availBW = self.availabilityUnderDC[1]
	# 		if availVMs >= vms and availBW >= bw:
	# 			# need to pick the device in this case
	# 			# if self.alloc(self.devices[_id], vms, bw):
	# 				# return True
	# 			return True

	# 	return False

	def allocate(self, traffic):
		assert isinstance(traffic, Traffic)

		if isinstance(traffic, Tenant):
			if cfg.defaultAllocationStrategy == AllocationStrategy.OKTOPUS:
				if not self.oktopus(traffic.numVMs, traffic.bw, traffic):
					return False
				else:
					self._addTraffic(traffic) # temporarily add, before checking for backups. if no backups, then later remove.
					if cfg.defaultBackupStrategy == BackupStrategy.END_TO_END:
						globals.simulatorLogger.debug("Looking for Tor_to_Tor backup(s) for Tenant = " + str(traffic.getID()) + ".")
						path = Path()
						hosts = []
						
						for host in traffic.getHosts():
							hosts.append(host)

						for link in traffic.getLinks():
							path.append(link)

						for switch in traffic.getSwitches():
							path.append(switch)

						if len(hosts) == 1:
							globals.simulatorLogger.debug("Tenant = " + str(traffic.getID()) + " has all VMs under same Host. No backup paths needed.")
							globals.simulatorLogger.debug("Adding Tenant = " + str(traffic.getID()) + " to traffic list.")
							# add the generated traffic to the list of traffics in topology
							return True

						for i in range(len(hosts)):
							for j in range(i+1,len(hosts)):
								assert hosts[i] != hosts[j] # make sure both hosts are not the same

								startSW = hosts[i].getLink().getOtherDevice(hosts[i])
								endSW = hosts[j].getLink().getOtherDevice(hosts[j])

								if startSW == endSW:
									# if both are under same tor, then no backups
									globals.simulatorLogger.debug("Tenant = " + str(traffic.getID()) + " has all VMs under same Tor. No backup paths possible.")
									globals.simulatorLogger.debug("Adding Tenant = " + str(traffic.getID()) + " to traffic list.")
									# added the generated traffic to the list of traffics in topology
									return True
								
								# TODO: BW should be the min of the number of VMs on hosts[i] and hosts[j] -- use tenant.hostsAndNumVMs here
								disjointPath = self.findDisjointPath(hosts[i].getID(), hosts[j].getID(), traffic.bw, [path])
								if disjointPath is None:
									self.deallocate(traffic.getID())
									globals.simulatorLogger.warning("Tenant = " + str(traffic.getID()) + " rejected due to unavailability of backup path(s).")
									return False
								else:
									# backup found
									# TODO: reserve bandwidth on backup too now
									globals.simulatorLogger.debug("Backup path(s) found for Tenant = " + str(traffic.getID()) + ".")
									globals.simulatorLogger.debug("Adding Tenant = " + str(traffic.getID()) + " to traffic list.")
									# added the generated traffic to the list of traffics in topology
									return True
					else:
						globals.simulatorLogger.debug("No backup(s) requested for Tenant = " + str(traffic.getID()) + ".")
						globals.simulatorLogger.debug("Adding Tenant = " + str(traffic.getID()) + " to traffic list.")
						# added the generated traffic to the list of traffics in topology
						return True


	def deallocate(self, trafficID):
		globals.simulatorLogger.debug("==========================")
		traffic = self.getAllTraffic().get(trafficID)
		if isinstance(traffic, Tenant):
			if traffic is not None:
				linksAndBw = traffic.getLinksAndBw()
				hostsAndNumVMs = traffic.getHostsAndNumVMs()
				globals.simulatorLogger.debug("Deallocating for trafficID = " + str(trafficID))
				for _id, data in linksAndBw.iteritems():
					# data[0] is the link object
					# data[1] is the BW that was reserved by this tenant on that link
					data[0].unReserveBW_AB(data[1])
					data[0].unReserveBW_BA(data[1])
					globals.simulatorLogger.debug("Deallocating BW = " + str(data[1]) + " from linkID =  " + str(_id))

				for vm in traffic.getVMs():
					assert vm.getTrafficID() == trafficID
					vm.setStatus(Status.AVAILABLE)
					vm.setID(None)
					globals.simulatorLogger.debug("Deallocating VM from hostID = " + str(vm.getHostID()))
				
				# delete the traffic from the list of traffics in topology after successfully deallocating
				self._removeTraffic(traffic)
				globals.simulatorLogger.debug("Deallocated trafficID: " + str(trafficID) + " successfully.")
				globals.simulatorLogger.debug("==========================")
				return True
			else:
				globals.simulatorLogger.error("Deallocating traffic that does not exist.")
				assert traffic is not None # to halt simulator if this occurs
			return False
		else:
			raise NotImplementedError

	
	# *** OKTOPUS STARTS HERE ***
	def getDownLinks(self, switch):
		downLinks = []
		
		if switch.getLabel() == "tor":
			for link in switch.getAllLinks():
				if link.getOtherDevice(switch).getLabel() == "host":
					downLinks.append(link)

		if switch.getLabel() == "aggr":
			for link in switch.getAllLinks():
				if link.getOtherDevice(switch).getLabel() == "tor":
					downLinks.append(link)

		if switch.getLabel() == "core":
			for link in switch.getAllLinks():
				if link.getOtherDevice(switch).getLabel() == "aggr":
					downLinks.append(link)

		return downLinks

	def computeMx(self, link, switch, bw):
		# checks the number of VMs that can be placed in a host, that also meet the BW requirements
		assert switch.getLabel() == "tor"
		residualBW = link.getMinAvailableBW()
		cap = residualBW/bw
		host = link.getOtherDevice(switch)
		hostVM = len(host.getAvailableVMs()) # available VMs in host
		canAllocate = min(cap, hostVM)
		return canAllocate

	def vmCount(self, device, bw):
		# counts the number of VMs under device that meet bandwidth requirement
		count = 0
		if device.getLabel() == "host":
			count = len(device.getAvailableVMs())
			return count
		if device.getLabel() == "tor":
			for link in self.getDownLinks(device):
				count = count + self.computeMx(link, device, bw)
			return count
		if device.getLabel() == "aggr":
			for link in self.getDownLinks(device):
				tor = link.getOtherDevice(device)
				val = self.vmCount(tor, bw)
				if link.getMinAvailableBW() < val*bw:
					return 0
				count = count + val
			return count
		if device.getLabel() == "core":
			for link in self.getDownLinks(device):
				aggr = link.getOtherDevice(device)
				val = self.vmCount(aggr, bw)
				if link.getMinAvailableBW() < val*bw:
					return 0
				count = count + val
			return count

	def oktopus(self, numVMs, bw, tenant):
		assert(numVMs != 0)
		globals.simulatorLogger.debug("==========================")
		globals.simulatorLogger.debug("Request for VMs = " + str(numVMs) + " and BW = " + str(bw) + " by Tenant = " + str(tenant.getID()) + " has arrived.")
		hosts = self.getAllHosts()
		for host in hosts:
			Mv = self.vmCount(host, bw)
			if numVMs <= Mv:
				globals.simulatorLogger.debug("Allocating under Host:")
				globals.simulatorLogger.debug(host.getID())
				allocated = self.alloc(host, numVMs, bw, tenant)
				globals.simulatorLogger.debug("Successfully allocated VMs = " + str(allocated) + " and BW = " + str(bw) + " for Tenant = " + str(tenant.getID()) + ".")
				globals.simulatorLogger.debug("==========================")
				return True
		
		tors = self.getAllTors()
		for tor in tors:
			Mv = self.vmCount(tor, bw)
			if numVMs <= Mv:
				globals.simulatorLogger.debug("Allocating under Tor:")
				globals.simulatorLogger.debug(tor.getID())
				allocated = self.alloc(tor, numVMs, bw, tenant)
				globals.simulatorLogger.debug("Successfully allocated VMs = " + str(allocated) + " and BW = " + str(bw) + " for Tenant = " + str(tenant.getID()) + ".")
				globals.simulatorLogger.debug("==========================")
				return True
		
		aggrs = self.getAllAggrs()
		for aggr in aggrs:
			Mv = self.vmCount(aggr, bw)
			if numVMs <= Mv:
				globals.simulatorLogger.debug("Allocating under Aggr:")
				globals.simulatorLogger.debug(aggr.getID())
				allocated = self.alloc(aggr, numVMs, bw, tenant)
				globals.simulatorLogger.debug("Successfully allocated VMs = " + str(allocated) + " and BW = " + str(bw) + " for Tenant = " + str(tenant.getID()) + ".")
				globals.simulatorLogger.debug("==========================")
				return True

		cores = self.getAllCores()
		for core in cores:
			Mv = self.vmCount(core, bw)
			if numVMs<= Mv:
				globals.simulatorLogger.debug("Allocating under Core:")
				globals.simulatorLogger.debug(core.getID())
				allocated = self.alloc(core, numVMs, bw, tenant)
				globals.simulatorLogger.debug("Successfully allocated VMs = " + str(allocated) + " and BW = " + str(bw) + " for Tenant = " + str(tenant.getID()) + ".")
				globals.simulatorLogger.debug("==========================")
				return True
		
		globals.simulatorLogger.warning("Tenant = " + str(tenant.getID()) + " could not be allocated.")
		globals.simulatorLogger.debug("==========================")
		return False

	def alloc(self, device, numVMs, bw, tenant):
		assert(numVMs != 0)
		if device.getLabel() == "host":
			link = device.getLink()
			residualBW = link.getMinAvailableBW()
			cap = residualBW/bw
			hostVM = len(device.getAvailableVMs()) # available VMs in host
			canAllocate = min(cap, hostVM)
			if canAllocate > numVMs:
				canAllocate = numVMs
			availableVMs = device.getAvailableVMs()
			for i in range(canAllocate):
				availableVMs[i].setStatus(Status.IN_USE)
				availableVMs[i].setID(tenant.getID())
				tenant.addVM(availableVMs[i])
			tenant.addHost(device, canAllocate)
			globals.simulatorLogger.debug(str(canAllocate) + " VMs placed under the following host:")
			globals.simulatorLogger.debug(device.getID())
			return canAllocate
		else:
			count = 0
			allocatedOnEachLink = []
			linksUsed = []
			for link in self.getDownLinks(device):
				otherDevice = link.getOtherDevice(device)
				Mx = self.vmCount(otherDevice, bw)
				if Mx == 0:
					continue
				if numVMs - count > 0:
					allocated = self.alloc(otherDevice, min(Mx, numVMs-count), bw, tenant)
					
					if device not in tenant.getSwitches():
						tenant.addSwitch(device)

					allocatedOnEachLink.append(allocated)
					linksUsed.append(link)
					count = count + allocated
			# takes the minimum of what was allocated below this device
			# and reserves that much bandwidth on the links used below this device
			bwOnEachLink = min(allocatedOnEachLink)*bw
			for link in linksUsed:
				link.reserveBW_AB(bwOnEachLink)
				link.reserveBW_BA(bwOnEachLink)
				tenant.addLink(link, bwOnEachLink)
				globals.simulatorLogger.debug(str(bwOnEachLink) + " BW reserved on the following link:")
				globals.simulatorLogger.debug(link.getID())
			return count
