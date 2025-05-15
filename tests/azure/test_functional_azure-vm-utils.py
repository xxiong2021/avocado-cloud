import os
import re
import time
import yaml
from avocado import Test
from avocado import main
# from avocado_cloud.app import Setup
# from avocado_cloud.app.azure import AzureAccount
# from avocado_cloud.app.azure import AzureNIC
from avocado_cloud.app.azure import AzurePublicIP
# from avocado_cloud.app.azure import AzureNicIpConfig
# from avocado_cloud.app.azure import AzureImage
from distutils.version import LooseVersion
# from avocado_cloud.utils import utils_azure


# import requests
# from avocado_cloud.utils.utils_azure import command


#BASEPATH = os.path.abspath(__file__ + "/../../../")


# class D(dict):
#     # Don't raise exception if cannot get key value
#     def __missing__(self, key):
#         self[key] = D()
#         return self[key]


class Azure_vm_utilsTest(Test):
    # def setUp(self):
    #     account = AzureAccount(self.params)
    #     account.login()
    #     self.project = self.params.get("rhel_ver", "*/VM/*")
    #     self.case_short_name = re.findall(r"Test.(.*)", self.name.name)[0]
    #     self.pwd = os.path.abspath(os.path.dirname(__file__))
        
    #     # Skip tests based on RHEL version
    #     if LooseVersion(self.project) < LooseVersion('9.7.0'):
    #         self.cancel(f"Skip case because RHEL-{self.project} doesn't support this feature")
    #     if LooseVersion(self.project) < LooseVersion('10.1'):
    #         self.cancel(f"Skip case because RHEL-{self.project} doesn't support this feature")
        
    #     # Initialize public IP and VM details
    #     publicip = AzurePublicIP(self.params, name=self.vm.vm_name)
    #     return

    # @property
    def _postfix(self):
        from datetime import datetime
        return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")

    def test_selftest_without_imds_symlink_validation(self):
        """
        :avocado: tags=tier1,azure_vm_utils
        """
        try:
            publicip = AzurePublicIP(self.params, name=self.vm.vm_name)
            self.log.info("publicip: %s",publicip)

            # Upload the selftest.py to the remote VM
            upload_command = "scp -i /root/.ssh/id_rsa /root/azure-vm-utils/selftest/selftest.py azureuser@{publicip}:/home/azureuser"
            command(upload_command)
            
            # Run the selftest.py script on the VM
            run_command = "ssh -i ./id_rsa azureuser@{publicip} -- sudo /home/azureuser/selftest.py --skip-imds-validation --skip-symlink-validation > result.txt 2>&1"
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

      
