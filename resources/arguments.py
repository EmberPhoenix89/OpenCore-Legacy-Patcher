import argparse
import sys
import subprocess
from resources import defaults, build
from data import example_data, model_array

# Generic building args
class arguments:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--build", help="Build OpenCore", action="store_true", required=False)
        parser.add_argument("--verbose", help="Enable verbose boot", action="store_true", required=False)
        parser.add_argument("--debug_oc", help="Enable OpenCore DEBUG", action="store_true", required=False)
        parser.add_argument("--debug_kext", help="Enable kext DEBUG", action="store_true", required=False)
        parser.add_argument("--hide_picker", help="Hide OpenCore picker", action="store_true", required=False)
        parser.add_argument("--disable_sip", help="Disable SIP", action="store_true", required=False)
        parser.add_argument("--disable_smb", help="Disable SecureBootModel", action="store_true", required=False)
        parser.add_argument("--vault", help="Enable OpenCore Vaulting", action="store_true", required=False)
        parser.add_argument("--support_all", help="Allow OpenCore on natively supported Models", action="store_true", required=False)
        parser.add_argument("--firewire", help="Enable FireWire Booting", action="store_true", required=False)
        parser.add_argument("--nvme", help="Enable NVMe Booting", action="store_true", required=False)
        parser.add_argument("--wlan", help="Enable Wake on WLAN support", action="store_true", required=False)
        # parser.add_argument("--disable_amfi", help="Disable AMFI", action="store_true", required=False)
        parser.add_argument("--moderate_smbios", help="Moderate SMBIOS Patching", action="store_true", required=False)
        parser.add_argument("--moj_cat_accel", help="Allow Root Patching on Mojave and Catalina", action="store_true", required=False)
        parser.add_argument("--disable_tb", help="Disable Thunderbolt on 2013-2014 MacBook Pros", action="store_true", required=False)
        parser.add_argument("--force_surplus", help="Force SurPlus in all newer OSes", action="store_true", required=False)

        # Building args requiring value values (ie. --model iMac12,2)
        parser.add_argument("--model", action="store", help="Set custom model", required=False)
        parser.add_argument("--disk", action="store", help="Specifies disk to install to", required=False)
        parser.add_argument("--smbios_spoof", action="store", help="Set SMBIOS patching mode", required=False)

        # sys_patch args
        parser.add_argument("--patch_sys_vol", help="Patches root volume", action="store_true", required=False)
        parser.add_argument("--unpatch_sys_vol", help="Unpatches root volume, EXPERIMENTAL", action="store_true", required=False)

        # validation args
        parser.add_argument("--validate", help="Runs Validation Tests for CI", action="store_true", required=False)
        self.args = parser.parse_args()

    def check_cli(self):
        # If no core arguments are present, assume we're running in TUI
        # build, patch_sys_vol, unpatch_sys_vol, validate
        if not(
            self.args.build or self.args.patch_sys_vol or self.args.unpatch_sys_vol or self.args.validate
        ):
            return False
        else:
            return True
    
    def parse_arguments(self, settings):
        if self.args.model:
            if self.args.model:
                print(f"- Using custom model: {self.args.model}")
                settings.custom_model = self.args.model
                defaults.generate_defaults.probe(settings.custom_model, False, settings)
            elif settings.computer.real_model not in model_array.SupportedSMBIOS and settings.allow_oc_everywhere is False:
                print(
                    """Your model is not supported by this patcher for running unsupported OSes!"

If you plan to create the USB for another machine, please select the "Change Model" option in the menu."""
                )
                sys.exit(1)
            else:
                print(f"- Using detected model: {settings.computer.real_model}")
                defaults.generate_defaults.probe(settings.custom_model, True, settings)

        if self.args.disk:
            print(f"- Install Disk set: {self.args.disk}")
            settings.disk = self.args.disk
        if self.args.validate:
            self.validate(settings)
        if self.args.verbose:
            print("- Set verbose configuration")
            settings.verbose_debug = True
        else:
            settings.verbose_debug = False # Override Defaults detected
        if self.args.debug_oc:
            print("- Set OpenCore DEBUG configuration")
            settings.opencore_debug = True
            settings.opencore_build = "DEBUG"
        if self.args.debug_kext:
            print("- Set kext DEBUG configuration")
            settings.kext_debug = True
        if self.args.hide_picker:
            print("- Set HidePicker configuration")
            settings.showpicker = False
        if self.args.disable_sip:
            print("- Set Disable SIP configuration")
            settings.sip_status = False
        else:
            settings.sip_status = True # Override Defaults detected
        if self.args.disable_smb:
            print("- Set Disable SecureBootModel configuration")
            settings.secure_status = False
        else:
            settings.secure_status = True # Override Defaults detected
        if self.args.vault:
            print("- Set Vault configuration")
            settings.vault = True
        if self.args.firewire:
            print("- Set FireWire Boot configuration")
            settings.firewire_boot = True
        if self.args.nvme:
            print("- Set NVMe Boot configuration")
            settings.nvme_boot = True
        # if self.args.disable_amfi:
        #     print("- Set Disable AMFI configuration")
        #     settings.amfi_status = False
        if self.args.wlan:
            print("- Set Wake on WLAN configuration")
            settings.enable_wake_on_wlan = True
        if self.args.disable_tb:
            print("- Set Disable Thunderbolt configuration")
            settings.disable_tb = True
        if self.args.force_surplus:
            print("- Forcing SurPlus override configuration")
            settings.force_surplus = True
        if self.args.moderate_smbios:
            print("- Set Moderate SMBIOS Patching configuration")
            settings.serial_settings = "Moderate"
        if self.args.smbios_spoof:
            if self.args.smbios_spoof == "Minimal":
                settings.serial_settings = "Minimal"
            elif self.args.smbios_spoof == "Moderate":
                settings.serial_settings = "Moderate"
            elif self.args.smbios_spoof == "Advanced":
                settings.serial_settings = "Advanced"
            else:
                print(f"- Unknown SMBIOS arg passed: {self.args.smbios_spoof}")

        if self.args.support_all:
            print("- Building for natively supported model")
            settings.allow_oc_everywhere = True
            settings.serial_settings = "None"

        # Avoid running the root patcher if we're just building
        if self.args.build:
            build.BuildOpenCore(settings.custom_model, settings).build_opencore()
        elif self.args.patch_sys_vol:
            if self.args.moj_cat_accel:
                print("- Set Mojave/Catalina root patch configuration")
                settings.moj_cat_accel = True
            print("- Set System Volume patching")
            self.patch_vol()
        elif self.args.unpatch_sys_vol:
            print("- Set System Volume unpatching")
            self.unpatch_vol()

    def validate(self, settings):
        # Runs through ocvalidate to check for errors

        valid_dumps = [
            example_data.MacBookPro.MacBookPro92_Stock,
            # example_data.MacBookPro.MacBookPro171_Stock,
            # example_data.Macmini.Macmini91_Stock,
            example_data.iMac.iMac81_Stock,
            example_data.iMac.iMac112_Stock,
            example_data.iMac.iMac122_Upgraded,
            example_data.MacPro.MacPro31_Stock,
            example_data.MacPro.MacPro31_Upgrade,
            example_data.MacPro.MacPro31_Modern_AMD,
            example_data.MacPro.MacPro31_Modern_Kepler,
            example_data.MacPro.MacPro41_Upgrade,
            example_data.MacPro.MacPro41_Modern_AMD,
            example_data.MacPro.MacPro41_51__Flashed_Modern_AMD,
        ]
        settings.validate = True
        def build_prebuilt():
            for model in model_array.SupportedSMBIOS:
                print(f"Validating predefined model: {model}")
                settings.custom_model = model
                build.BuildOpenCore(settings.custom_model, settings).build_opencore()
                result = subprocess.run([settings.ocvalidate_path, f"{settings.opencore_release_folder}/EFI/OC/config.plist"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if result.returncode != 0:
                    print("Error on build!")
                    print(result.stdout.decode())
                    raise Exception(f"Validation failed for predefined model: {model}")
                else:
                    print(f"Validation succeeded for predefined model: {model}")
        
        def build_dumps():
            for model in valid_dumps:
                settings.computer = model
                settings.custom_model = ""
                print(f"Validating dumped model: {settings.computer.real_model}")
                build.BuildOpenCore(settings.computer.real_model, settings).build_opencore()
                result = subprocess.run([settings.ocvalidate_path, f"{settings.opencore_release_folder}/EFI/OC/config.plist"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if result.returncode != 0:
                    print("Error on build!")
                    print(result.stdout.decode())
                    raise Exception(f"Validation failed for predefined model: {settings.computer.real_model}")
                else:
                    print(f"Validation succeeded for predefined model: {settings.computer.real_model}")
        
        # First run is with default settings
        build_prebuilt()
        build_dumps()
        # Second run, flip all settings
        settings.verbose_debug = True
        settings.opencore_debug = True
        settings.opencore_build = "DEBUG"
        settings.kext_debug = True
        settings.showpicker = False
        settings.sip_status = False
        settings.secure_status = True
        settings.firewire_boot = True
        settings.nvme_boot = True
        settings.enable_wake_on_wlan = True
        settings.disable_tb = True
        settings.force_surplus = True
        build_prebuilt()
        build_dumps()





