LPM_MODULES_FOLDER=$(srctree)/drivers/misc/mediatek/lpm/modules/


ccflags-y += -I$(LPM_MODULES_FOLDER)/include/


MTK_LPM_MODULE_PLATFORM_PLAT_NAME=v1
MTK_LPM_SUSPEND_VERSION = suspend_v1


ccflags-y += -I$(LPM_MODULES_FOLDER)/platform/$(MTK_LPM_PLATFORM_VERSION)/
ccflags-y += -I$(LPM_MODULES_FOLDER)/platform/$(MTK_LPM_SUSPEND_VERSION)/
ccflags-y += -I$(LPM_MODULES_FOLDER)/include/
#source files
LPM_MODULE_PLAT_PLATFORM_SUSPEND_OBJS += lpm_plat_suspend.o
