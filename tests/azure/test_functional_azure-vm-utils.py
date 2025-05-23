import os
import re
import time
import yaml
import json
from avocado import Test
from avocado import main
from avocado_cloud.app import Setup
# from avocado_cloud.app.azure import AzureAccount
# from avocado_cloud.app.azure import AzureNIC
from avocado_cloud.app.azure import AzurePublicIP
from avocado_cloud.app.azure import AzureNicIpConfig
# from avocado_cloud.app.azure import AzureImage
from distutils.version import LooseVersion
from avocado_cloud.utils import utils_azure


# import requests
from avocado_cloud.utils.utils_azure import command


BASEPATH = os.path.abspath(__file__ + "/../../../")


# class D(dict):
#     # Don't raise exception if cannot get key value
#     def __missing__(self, key):
#         self[key] = D()
#         return self[key]


class Azure_vm_utilsTest(Test):

    def _postfix(self):
        from datetime import datetime
        return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")

    def setUp(self):
        self.cloud = Setup(self.params, self.name)
        self.vm = self.cloud.vm  # Access the VM created during setup
        authentication = "publickey"
        self.session = self.cloud.init_vm(authentication=authentication)
        #publicip_name = self.vm.vm_name + "PublicIP"
        # self.log.info("publicip_name: %s",publicip_name)
        # #publicip = AzurePublicIP(self.params,name=publicip_name)
        # #self.log.info("publicip: %s",publicip)
        # publicip = AzurePublicIP(self.params, name=publicip_name)
        # if not publicip.exists():
        #     publicip.create()
        # account = AzureAccount(self.params)
        # account.login()
        # cloud = Setup(self.params, self.name)
        # self.vm = cloud.vm
        # self.session = cloud.init_vm()
        # status, output = self.session.cmd_status_output('uname -r')
        #authentication = "publickey"
        # info = json.loads(ret.stdout)
        # public_ip = info["publicIpAddress"]
        
        # ret = publicip.show()
        # info = json.loads(ret.stdout)
        # public_ip = info["ipAddress"]
        #public_ip = self.vm.public_ip
        
        # try:
        #     ret = command(cmd)
        # except:
        # time.sleep(120)
        # cmd = ' az network public-ip show   --name {} --resource-group "{}" '.format(publicip_name, self.vm.resource_group)
        # ret = command(cmd)
        # info = json.loads(ret.stdout)
        # public_ip = info["ipAddress"]
        
            
        # retry_count = int(self.params.get("retry_count", default=5))
        # delay_seconds = int(self.params.get("delay_seconds", default=5))

        # publicip = ""
        # for attempt in range(retry_count):
        #     ret = command(cmd)
        #     publicip = ret.stdout.strip()
        #     if publicip:
        #         break
        #     self.log.warning("Public IP not yet assigned (attempt %d). Retrying in %d seconds...", attempt + 1, delay_seconds)
        #     time.sleep(delay_seconds)

        # if not publicip:
        #     raise RuntimeError("Public IP address is empty or not assigned after retries.")


    def test_selftest_without_imds_symlink_validation(self):
        """
        :avocado: tags=tier1,azure_vm_utils
        """
        try:
            #publicip = AzurePublicIP(self.params, name=self.vm.vm_name)
            #self.log.info("publicip: %s",publicip)
            if self.vm.exists():
                self.vm.delete()
            file_path = '/root/azure-vm-utils/result.txt'
            if os.path.exists(file_path):
                os.remove(file_path)
    
            key = "/root/.ssh/id_rsa.pub"
            self.vm.ssh_key_value = "{}".format(key)
            self.vm.authentication_type = "ssh"
            self.vm.vm_name += "-utils"
            self.vm.create(wait=True)
            self.session.connect(authentication="publickey")
            self.assertEqual(self.vm.vm_username,
                             self.session.cmd_output("whoami"),
                             "Fail to login with publickey")
            self.assertIn(
                "%s ALL=(ALL) NOPASSWD:ALL" % self.vm.vm_username,
                self.session.cmd_output(
                    "sudo cat /etc/sudoers.d/90-cloud-init-users"),
                "No sudo privilege")
            
            publicip_name = self.vm.vm_name + "PublicIP"
            cmd = ' az network public-ip show   --name {} --resource-group "{}"  --query "ipAddress"   --output tsv'.format(publicip_name, self.vm.resource_group)
            ret = command(cmd)
            public_ip = ret.stdout.strip()
            self.log.info("public_ip: %s", public_ip)

            # Upload the selftest.py to the remote VM
            upload_command = 'scp -i /root/.ssh/id_rsa /root/azure-vm-utils/selftest/selftest.py azureuser@{}:/home/azureuser'.format(public_ip)
            command(upload_command)
            
            # Run the selftest.py script on the VM
            run_command = 'ssh -i ./id_rsa azureuser@{} -- sudo /home/azureuser/selftest.py --skip-imds-validation --skip-symlink-validation > result.txt 2>&1'.format(public_ip)
            command(run_command)
            
            # Get the last line of the result
            result_command = "tail -n 1 /root/azure-vm-utils/result.txt | awk '{print $NF}'"
            ret = command(result_command)
            
            
            # Check if the result was successful
            if ret.stdout.strip() == "success!":
                self.log.info("Self-test completed successfully.")
                self.vm.delete()
                return True
            else:
                self.log.error("Self-test failed: {}".format(ret.stdout))
                self.vm.delete()
                return False
        
        except Exception as e:
            self.log.error("An error occurred: {}".format(str(e)))
            return False

    def tearDown(self):
        self.vm.delete()

if __name__ == "__main__":
    main()
