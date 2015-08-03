  #--------------#
    #-- CLONE VM --#
    #--------------#
    def clone(self, name, sync_run=True, folder=None, resourcepool=None,
              power_on=True, template=False, customize=None):
        """Clones this Virtual Machine
        @name: name of the new virtual machine
        @folder: name of the folder that will contain the new VM, if not set
                 the vm will be added to the folder the original VM belongs to
        @resourcepool: MOR of the resourcepool to be used for the new vm. 
                 If not set, it uses the same resourcepool than the original vm.
        @power_on: If the new VM will be powered on after being created
        @sync_run: if True (default) waits for the task to finish, and returns
        a VIVirtualMachine instance with the new VM (raises an exception if the
        task didn't succeed). If sync_run is set to False the task is started an
        a VITask instance is returned
        """
        try:
            #get the folder to create the VM
            folders = self._server._retrieve_properties_traversal(
                                         property_names=['name', 'childEntity'],
                                         obj_type=MORTypes.Folder)
            folder_mor = None
            for f in folders:
                fname = ""
                children = []
                for prop in f.PropSet:
                    if prop.Name == "name":
                        fname = prop.Val
                    elif prop.Name == "childEntity":
                        children = prop.Val.ManagedObjectReference
                if folder == fname or (not folder and self._mor in children):
                    folder_mor = f.Obj
                    break
            if not folder_mor and folder:
                raise VIException("Couldn't find folder %s" % folder,
                                  FaultTypes.OBJECT_NOT_FOUND)
            elif not folder_mor:
                raise VIException("Error locating current VM folder",
                                  FaultTypes.OBJECT_NOT_FOUND)
    
            request = VI.CloneVM_TaskRequestMsg()
            _this = request.new__this(self._mor)
            _this.set_attribute_type(self._mor.get_attribute_type())
            request.set_element__this(_this)
            request.set_element_folder(folder_mor)
            request.set_element_name(name)
            spec = request.new_spec()
            spec.set_element_powerOn(power_on)
            location = spec.new_location()
            if resourcepool:
                if not VIMor.is_mor(resourcepool):
                    resourcepool = VIMor(resourcepool, MORTypes.ResourcePool)
                pool = location.new_pool(resourcepool)
                pool.set_attribute_type(resourcepool.get_attribute_type())
                location.set_element_pool(pool)
            spec.set_element_location(location)
            spec.set_element_template(template)

            if not template and customize == "WIN":
                customization = spec.new_customization()
                spec.set_element_customization(customization)

                globalIPSettings = customization.new_globalIPSettings()
                customization.set_element_globalIPSettings(globalIPSettings)

                identity = VI.ns0.CustomizationSysprep_Def("identity").pyclass()
                customization.set_element_identity(identity)

                # nicSettingMap
                nicSetting = customization.new_nicSettingMap()
                adapter = nicSetting.new_adapter()
                nicSetting.set_element_adapter(adapter)
                dhcp = VI.ns0.CustomizationDhcpIpGenerator_Def("ip").pyclass()
                adapter.set_element_ip(dhcp)
                customization.set_element_nicSettingMap([nicSetting,])

                guiUnattended = identity.new_guiUnattended()
                guiUnattended.set_element_autoLogon(True)
                guiUnattended.set_element_autoLogonCount(1)

                passw = guiUnattended.new_password()
                guiUnattended.set_element_password(passw)
                passw.set_element_value("MyDefaultAdminPassword")
                passw.set_element_plainText(True)

                # http://msdn.microsoft.com/en-us/library/ms912391(v=winembedded.11).aspx
                guiUnattended.set_element_timeZone(85) # GMT Standard Time
                identity.set_element_guiUnattended(guiUnattended)

                userData = identity.new_userData()
                userData.set_element_fullName("PySphere")
                userData.set_element_orgName("PySphere")
                userData.set_element_productId("")
                computerName = VI.ns0.CustomizationFixedName_Def("computerName").pyclass()
                computerName.set_element_name(name.replace("_", ""))
                userData.set_element_computerName( computerName )
                identity.set_element_userData(userData)

                identification = identity.new_identification()

                # join the domain
                identification.set_element_domainAdmin("MyDomainAdminUser")
                domainAdminPassword = identification.new_domainAdminPassword()
                domainAdminPassword.set_element_plainText(True)
                domainAdminPassword.set_element_value("MyDomainAdminPassword")
                identification.set_element_domainAdminPassword(domainAdminPassword)
                identification.set_element_joinDomain("MyDomain")
                identity.set_element_identification(identification)


            request.set_element_spec(spec)
            task = self._server._proxy.CloneVM_Task(request)._returnval
            vi_task = VITask(task, self._server)
            if sync_run:
                status = vi_task.wait_for_state([vi_task.STATE_SUCCESS,
                                                 vi_task.STATE_ERROR])
                if status == vi_task.STATE_ERROR:
                    raise VIException(vi_task.get_error_message(),
                                      FaultTypes.TASK_ERROR)
                return VIVirtualMachine(self._server, vi_task.get_result()) 
                
            return vi_task

        except (VI.ZSI.FaultException), e:
            raise VIApiException(e)