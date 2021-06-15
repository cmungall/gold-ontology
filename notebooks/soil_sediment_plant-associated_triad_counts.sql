select
	env_package ,
	env_broad_scale ,
	env_broad_scale_label,
	env_local_scale ,
	env_local_scale_label ,
	env_medium ,
	env_medium_label ,
	count(1)
from
	repaired_mixs_plus_soil_sediment_pa rmpssp
group by
	env_package ,
	env_broad_scale ,
	env_broad_scale_label,
	env_local_scale ,
	env_local_scale_label ,
	env_medium,
	env_medium_label
order by
	count(1) desc;