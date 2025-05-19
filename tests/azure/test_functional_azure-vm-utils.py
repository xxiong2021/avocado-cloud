import os
import re
import time
import yaml
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
        publicip_name = self.vm.vm_name + "PublicIP"
        self.log.info("publicip_name: %s",publicip_name)
        #publicip = AzurePublicIP(self.params,name=publicip_name)
        #self.log.info("publicip: %s",publicip)
        cmd = ' az network public-ip show   --name {} --resource-group "{}"  --query "ipAddress"   --output tsv'.format(publicip_name, self.vm.resource_group)
        
        retry_count = int(self.params.get("retry_count", default=5))
        delay_seconds = int(self.params.get("delay_seconds", default=5))

        publicip = ""
        for attempt in range(retry_count):
            ret = command(cmd)
            publicip = ret.stdout.strip()
            if publicip:
                break
            self.log.warning("Public IP not yet assigned (attempt %d). Retrying in %d seconds...", attempt + 1, delay_seconds)
            time.sleep(delay_seconds)

        if not publicip:
            raise RuntimeError("Public IP address is empty or not assigned after retries.")
        self.publicip = publicip
        self.log.info("publicip: %s", self.publicip)

    def test_selftest_without_imds_symlink_validation(self):
        """
        :avocado: tags=tier1,azure_vm_utils
        """
        try:
            #publicip = AzurePublicIP(self.params, name=self.vm.vm_name)
            #self.log.info("publicip: %s",publicip)

            # Upload the selftest.py to the remote VM
            upload_command = 'scp -i /root/.ssh/id_rsa /root/azure-vm-utils/selftest/selftest.py azureuser@{}:/home/azureuser'.format(self.publicip)
            command(upload_command)
            
            # Run the selftest.py script on the VM
            run_command = 'ssh -i ./id_rsa azureuser@{} -- sudo /home/azureuser/selftest.py --skip-imds-validation --skip-symlink-validation > result.txt 2>&1'.format(self.publicip)
            command(run_command)
            
            # Get the last line of the result
            result_command = "tail -n 1 /root/azure-vm-utils/result.txt | awk '{print $NF}'"
            ret = command(result_command)
            
            # Check if the result was successful
            if ret.stdout.strip() == "success!":
                self.log.info("Self-test completed successfully.")
                return True
            else:
                self.log.error("Self-test failed: {}".format(ret.stdout))
                return False
        
        except Exception as e:
            self.log.error("An error occurred: {}".format(str(e)))
            return False

      
