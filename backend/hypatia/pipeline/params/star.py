import numpy as np

from hypatia.object_params import SingleParam, ObjectParams
from hypatia.tools.coordinates import spherical_astronomy_to_cartesian


class SingleStarParams:
    def __init__(self):
        self.available_params = set()
        self.all_params = {}

    def update_param(self, param_name: str, single_param: SingleParam, overwrite_existing: bool = False):
        if overwrite_existing or not hasattr(self, param_name):
            self.__setattr__(param_name, single_param)
            self.available_params.add(param_name)
        if param_name not in self.all_params:
            self.all_params[param_name] = set()
        self.all_params[param_name].add(single_param)

    def update_params(self, params_dict: ObjectParams, overwrite_existing=False):
        for param_name in params_dict.keys():
            for single_param in params_dict[param_name]:
                self.update_param(param_name=param_name, single_param=single_param,
                                  overwrite_existing=overwrite_existing)

    def to_dict(self):
        return {param_name: self.__getattribute__(param_name) for param_name in self.available_params}

    def to_record(self):
        return {param_name: {
            'curated': self.__getattribute__(param_name).to_record(param_name),
            'all': [single_param.to_record(param_name) for single_param in self.all_params[param_name]]
        } for param_name in self.available_params}

    def calculated_params(self, ref='Hypatia Calc'):
        """
        Calculations
        """
        dist = None
        ra = None
        dec = None

        if 'dist' in self.available_params:
            dist = self.dist.value

        # from Gaia
        if "ra_epochj2000" in self.available_params and "dec_epochj2000" in self.available_params:
            ra = self.ra_epochj2000.value
            dec = self.dec_epochj2000.value
        if 'parallax' in self.available_params:
            if 0.0 < self.parallax.value:
                if dist is None:
                    dist = 1.0 / (float(self.parallax.value * 0.001))
                    dist_single_param = SingleParam(value=dist,
                                                    ref=f'Hypatia Calc from parallax:{self.parallax.ref}',
                                                    units='[pc]')
                    self.update_param("dist", dist_single_param)
                    self.available_params.add("dist")
            else:
                self.__delattr__('parallax')
                self.available_params.remove("parallax")
        # from xHipparcos
        if ra is None and dec is None and "raj2000" in self.available_params and "decj2000" in self.available_params:
            ra = self.raj2000.value
            dec = self.decj2000.value
        # set the distance and position values
        if dist is not None and ra is not None and dec is not None:
                x_pos, y_pos, z_pos = spherical_astronomy_to_cartesian((ra, dec, dist))
                for pos_name, pos_value in zip(['x_pos', 'y_pos', 'z_pos'], [x_pos, y_pos, z_pos]):
                    pos_single_param = SingleParam(value=pos_value, ref='Hypatia Calc', units='[pc]')
                    self.update_param(pos_name, pos_single_param, overwrite_existing=True)
                    self.available_params.add(pos_name)

        # Thick Disk or Thin Disk stars
        if self.available_params.issuperset({"u_vel", "v_vel", "w_vel"}):
            kd = 1. / ((2. * np.pi) ** 1.5 * 35. * 20. * 16.)  # Calculations from Benbsy et al. (2003)
            ktd = 1. / ((2. * np.pi) ** 1.5 * 67. * 38. * 35.)
            ud = self.u_vel.value ** 2. / (2. * 35. ** 2.)
            vd = ((self.v_vel.value + 15.) ** 2.) / (2. * 20. ** 2.)
            wd = self.w_vel.value ** 2. / (2. * 16. ** 2.)
            ffd = kd * np.exp(-ud - vd - wd)
            #
            utd = self.u_vel.value ** 2. / (2. * 67. ** 2.)
            vtd = ((self.v_vel.value + 36.) ** 2.) / (2. * 38. ** 2.)
            wtd = self.w_vel.value ** 2. / (2. * 35. ** 2.)
            fftd = ktd * np.exp(-utd - vtd - wtd)
            #
            td_d = ((0.18 / 0.82) * (fftd / ffd))  # Value changed to match Adibekyan et al. (2013)
            if td_d > 10.:
                disk_value = 'thick'
                disk_num = 1
            else:
                disk_value = 'thin'
                disk_num = 0
        else:
            disk_value = "N/A"
            disk_num = None
        disk_single_param = SingleParam(value=disk_value, ref=ref, units='string')
        self.update_param('disk', disk_single_param, overwrite_existing=True)
        if disk_num is not None:
            new_param = SingleParam.strict_format(param_name='disk_num', value=disk_num ,ref=ref, units='')
            self.update_param('disk_num', new_param, overwrite_existing=True)
