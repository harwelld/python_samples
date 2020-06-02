USE [tfm]
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_GET_ChemicalOIDs_propertyOID]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Returns chemicalOID domain for a given property

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
01/07/2019	dharwell			Initial
04/01/2020  dharwell			Added way to handle empty domains by adding placeholder
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_GET_ChemicalOIDs_propertyOID]
	@propertyOID int
	
as

	set nocount on

	drop table if exists #temp;

	create table #temp(
		code varchar(50),
		description varchar(200)
	);

	insert into #temp
		select distinct CODE as 'code',
			case when charindex('--', description) > 0 then
			LEFT(description, charindex('--', description)-1) else  -- Removes the concatinated location in the description field to get name
			description end as 'description'
		from v_tfm_vt_act_Chem_MasterOID vm
		inner join TFM_ACT_Chemical_Master m
		on vm.CODE = m.ObjectID
		where vm.PropertyOID = @propertyOID and vm.activeflag = 1 and m.GTFF_Approved_IND = 'Y';

	if (select count(*) from #temp)=0 
		insert into #temp
		values ('1', 'NA');

	select * from #temp;
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_GET_CompartmentOIDs_propertyOID]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Returns compartmentOID domain for a given property

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
12/30/2019	dharwell			Initial
04/01/2020  dharwell			Added way to handle empty domains by adding placeholder
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_GET_CompartmentOIDs_propertyOID]
	@propertyOID int
	
as
	set nocount on

	drop table if exists #temp;

	create table #temp(
		code varchar(50),
		description varchar(200)
	);

	insert into #temp
		select CompartmentOID as 'code', description as 'description'
		from v_tfm_vt_cmn_Compartment_Name c
		where PropertyOID = @propertyOID and activeflag = 1;

	if (select count(*) from #temp)=0 
		insert into #temp
		values ('1', 'NA');

	select * from #temp;
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_GET_ContractorOIDs_propertyOID]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Returns contractorOID domain for a given property

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
12/30/2019	dharwell			Initial
04/01/2020  dharwell			Added way to handle empty domains by adding placeholder
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_GET_ContractorOIDs_propertyOID]
	@propertyOID int
	
as
	set nocount on

	drop table if exists #temp;

	create table #temp(
		code varchar(50),
		description varchar(200)
	);

	insert into #temp
		select distinct Contractor_OID as 'code', DESCRIPTION as 'description'
		from V_TFM_VT_ACT_Contractor_Rest
		where PROPERTYOID = @propertyOID and activeflag = 1;

	if (select count(*) from #temp)=0 
		insert into #temp
		values ('1', 'NA');

	select * from #temp;
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_GET_HardcodedLists_propertyOID]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Used for setting up a new Survey123 Activity Survey.
Returns lists that are hardcoded into 'choices' tab of survey for a given property:
CompartmentOID
Active Supervisors
Active Contractors

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
12/13/2019	dharwell			Initial
12/21/2019  dharwell			Modified to use compartment VT instead of base compartment table
02/12/2020  dharwell			Modified to return list_name field in result
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_GET_HardcodedLists_propertyOID]
	@propertyOID int
	
as
	set nocount on

	-- CompartmentOIDs
	select 'compartment' as 'list_name', CompartmentOID, description as 'Compartment'
	from v_tfm_vt_cmn_Compartment_Name c
	where PropertyOID = @propertyOID and activeflag = 1;

	-- Supervisor
	select distinct 'supervisor' as 'list_name', CODE, DESCRIPTION as 'Supervisor'
	from TFM_VT_CMN_Supervisor
	where PROPERTYOID = @propertyOID and ACTIVEFLAG = 1;

	-- Contractor
	select distinct 'contractor' as 'list_name', Contractor_OID, DESCRIPTION as 'Contractor'
	from V_TFM_VT_ACT_Contractor_Rest
	where PROPERTYOID = @propertyOID and activeflag = 1;
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_GET_PlantingSpecies_propertyOID]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Returns planting species domain for a given property

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
05/01/2020	dharwell			Initial
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_GET_PlantingSpecies_propertyOID]
	@propertyOID int
	
as
	set nocount on

	drop table if exists #temp;

	create table #temp(
		code varchar(50),
		description varchar(200)
	);

	insert into #temp
		select distinct SPECIES_CODE as 'code', SPECIES_DESC as 'description'
		from V_TFM_VT_Species_RES s
		where PropertyOID = @propertyOID and activeflag = 1;

	if (select count(*) from #temp)=0 
		insert into #temp
		values ('1', 'NA');

	select * from #temp;
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_GET_SupervisorOIDs_propertyOID]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Returns supervisorOID domain for a given property

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
12/30/2019	dharwell			Initial
04/01/2020  dharwell			Added way to handle empty domains by adding placeholder
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_GET_SupervisorOIDs_propertyOID]
	@propertyOID int
	
as
	set nocount on

	drop table if exists #temp;

	create table #temp(
		code varchar(50),
		description varchar(200)
	);

	insert into #temp
		select distinct CODE as 'code', DESCRIPTION as 'description'
		from TFM_VT_CMN_Supervisor
		where PROPERTYOID = @propertyOID and ACTIVEFLAG = 1;

	if (select count(*) from #temp)=0 
		insert into #temp
		values ('1', 'NA');

	select * from #temp;
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_GET_UniversalDomains]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Returns universal domains used in Collector layers:
CompartmentOID
Active Supervisors
Active Contractors
The purpose of this procedure is just to have these queries in one place, 
copy the results and save them as csvs used by the environment setup script.
Since some have translations, the csvs need to be manually created.

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
01/10/2020	dharwell			Initial
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_GET_UniversalDomains]
	
as
	set nocount on

	-- Activitiy Status
	select distinct CODE as 'code', DESCRIPTION as 'description'
	from V_TFM_VT_ACT_Status_Rest;

	-- Harvest Unit Status
	select distinct CODE as 'code', DESCRIPTION as 'description'
	from TFM_VT_HV_HarvStatus;

	-- Planting Pattern
	select distinct CODE as 'code', DESCRIPTION as 'description'
	from TFM_VT_CMN_Pattern;

	-- Planting Stock Type
	select distinct CODE as 'code', DESCRIPTION as 'description'
	from V_TFM_VT_CMN_Plant_Stock_Rest;

	-- Special Point
	select distinct concat(TYPE, ' - ' + SUBTYPE) as 'code',
					concat(TYPE_DESC, ' - ' + SubType_DESC) as 'description'
	from TFM_VT_CMN_SpecPoint_Type;

	-- Special Line
	select distinct concat(TYPE, ' - ' + SUBTYPE) as 'code',
					concat(TYPE_DESC, ' - ' + SubType_DESC) as 'description'
	from TFM_VT_CMN_SpecLine_Type

	-- Special Poly
	select distinct concat(TYPE, ' - ' + SUBTYPE) as 'code',
					concat(TYPE_DESC, ' - ' + SubType_DESC) as 'description'
	from TFM_VT_CMN_SpecPoly_Type;
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_Update_chemdefaults_propertyOID]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Returns default chemical cost as a lookup table by chemicalOID for a given property. Used by Survey123
pulldata() function to provide default value in survey.

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
12/12/2019	dharwell			Initial
12/13/2019  dharwell			Modified to include default application rate.
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_Update_chemdefaults_propertyOID]
	@propertyOID int
	
as
	set nocount on

	select Default_Cost_per_unit as 'cost',
		   DefaultRate as 'rate',
		   --ObjectID as 'chem_masterOID'
		   convert(decimal(16,1),(ObjectID/1.0)) as 'chem_masterOID'
	from TFM_ACT_Chemical_Master m
	inner join v_tfm_vt_act_Chem_MasterOID vm
	on m.ObjectID = vm.CODE
	where m.PropertyOID = @propertyOID and vm.activeflag = 1 and m.GTFF_Approved_IND = 'Y';
GO

/****** Object:  StoredProcedure [dbo].[MOBILE_Update_itemsets_propertyOID]    Script Date: 5/4/2020 11:01:30 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



/******************************************************************************************************
Created By: Dylan Harwell - Resource Data Inc

Returns unique category, type, subtype lists for property and stand activity domains, planting activity
species and variety domains, approved chemical inventory locations and chemical names in the format of
the Survey123 itemsets.csv file used for cascading selects.

Modifications:
Date		By					Description
-------------------------------------------------------------------------------------------------------
11/22/2019	dharwell			Initial
11/29/2019  dharwell			Modified to include 'prop_or_stand' column
12/05/2019	dharwell			Modified to include chemical inventory location and chemical name
12/10/2019  dharwell            Modified to use description field for label column
05/04/2020  dharwell			Modified to include planting species and variety
******************************************************************************************************/

CREATE procedure [dbo].[MOBILE_Update_itemsets_propertyOID]
	@propertyOID int
	
as
	set nocount on

	-- Clean temp tables
	if object_id('tempdb..#itemsets1') is not null
		drop table #itemsets1
	if object_id('tempdb..#itemsets2') is not null
		drop table #itemsets2
	if object_id('tempdb..#itemsets3') is not null
		drop table #itemsets3
	if object_id('tempdb..#itemsets4') is not null
		drop table #itemsets4
	if object_id('tempdb..#itemsets5') is not null
		drop table #itemsets5
	if object_id('tempdb..#itemsets6') is not null
		drop table #itemsets6
	if object_id('tempdb..#itemsets7') is not null
		drop table #itemsets7
	if object_id('tempdb..#itemsets8') is not null
		drop table #itemsets8
	if object_id('tempdb..#itemsets9') is not null
		drop table #itemsets9
	if object_id('tempdb..#itemsets10') is not null
		drop table #itemsets10
	if object_id('tempdb..#result') is not null
		drop table #result

	-- Create temp table formatted the same as itemsets.csv
	create table #itemsets1(
		list_name      varchar(25),
		name           varchar(100),
		label          varchar(100),
		p_category     varchar(100),
		p_type         varchar(100),
		s_category	   varchar(100),
		s_type		   varchar(100),
		prop_or_stand  varchar(25),
		s_subtype	   varchar(100),
		inv_loc		   varchar(100),
		REG_Species    varchar(100)
		);

	-- Table 1: PROPERTY CATEGORY
	-- This should be a list of active property activity categories for a given property
	-- Ignore 'p_category', 'prop' and all null fields
	insert into #itemsets1
		select distinct 'p_category', Category, Category_desc, null, null, null, null, 'prop', null, null, null
		from V_TFM_VT_OP_Property_TYPE_SUBTYPE_RES
		where PROPERTYOID = @propertyOID and activeflag = 1 and Category in 
			(select distinct category from V_TFM_VT_OP_Property_Category_1300
			 where PROPERTYOID = @propertyOID and activeflag = 1);

	-- Table 2: PROPERTY TYPE
	-- This should be a list of active property activity types (and associated category) for a given property
	-- Ignore 'p_type' and all null fields
	select top 0 * into #itemsets2 from #itemsets1
	insert into #itemsets2
		select distinct 'p_type', type, type_desc, Category, null, null, null, null, null, null, null
		from V_TFM_VT_OP_Property_TYPE_SUBTYPE_RES
		where PROPERTYOID = @propertyOID and activeflag = 1 and Category in 
			(select distinct category from V_TFM_VT_OP_Property_Category_1300
			 where PROPERTYOID = @propertyOID and activeflag = 1);

	-- Table 3: PROPERTY SUBTYPE
	-- This should be a list of active property activity subtypes (and associated type) for a given property
	-- Ignore 'p_subtype' and all null fields
	select top 0 * into #itemsets3 from #itemsets1
	insert into #itemsets3
		select distinct 'p_subtype', subtype, subTYpe_desc, null, type, null, null, null, null, null, null
		from V_TFM_VT_OP_Property_TYPE_SUBTYPE_RES
		where PROPERTYOID = @propertyOID and activeflag = 1 and Category in 
			(select distinct category from V_TFM_VT_OP_Property_Category_1300
			 where PROPERTYOID = @propertyOID and activeflag = 1);

	-- Table 4: STAND CATEGORY
	-- This should be a list of active stand activity categories for a given property
	-- Ignore 's_category', 'stand' and all null fields
	select top 0 * into #itemsets4 from #itemsets1
	insert into #itemsets4
		select distinct 's_category', Category, Category_desc, null, null, null, null, 'stand', null, null, null
		from dbo.V_TFM_VT_OP_Stand_1400
		where PROPERTYOID = @propertyOID and activeflag = 1;

	-- Table 5: STAND TYPE
	-- This should be a list of active stand activity types (and associated category) for a given property
	-- Ignore 's_type' and all null fields
	select top 0 * into #itemsets5 from #itemsets1
	insert into #itemsets5
		select distinct 's_type', type, type_desc, null, null, Category, null, null, null, null, null
		from dbo.V_TFM_VT_OP_Stand_1400
		where PROPERTYOID = @propertyOID and activeflag = 1;

	-- Table 6: STAND SUBTYPE
	-- This should be a list of active stand activity subtypes (and associated type) for a given property
	-- Ignore 's_subtype' and all null fields
	select top 0 * into #itemsets6 from #itemsets1
	insert into #itemsets6
		select distinct 's_subtype', subtype, subTYpe_desc, null, null, null, type, null, null, null, null
		from dbo.V_TFM_VT_OP_Stand_1400
		where PROPERTYOID = @propertyOID and activeflag = 1;

	-- Table 7: CHEMICAL INVENTORY LOCATION
	-- This should be a list of all active chemical inventory locations that have associated chemicals (and associated
	-- stand activity subtype) (some locations are marked active but have no chemicals) 
	select top 0 * into #itemsets7 from #itemsets1
	insert into #itemsets7
		select distinct 'inv_loc', vm.Inventory_Location, vm.Inventory_Location, null, null, null, null, null, s.subtype, null, null
		from TFM_VT_OP_ACT_TYPE s
		inner join v_tfm_vt_act_Chem_MasterOID vm on vm.PropertyOID = s.PROPERTYOID
		inner join TFM_ACT_Chemical_Master m on s.PROPERTYOID = m.PropertyOID
		where vm.propertyOID = @propertyOID and
			  vm.ACTIVEFLAG = 1 and 
			  s.ACTIVEFLAG = 1 and
			  IS_CHEMICAL_IND = 1 and
			  m.GTFF_Approved_IND = 'Y';

	-- Table 8: CHEMICAL NAME, INVENTORY LOCATION
	-- This should be a list of all active and approved chemical names and OIDs (and associated inventory locations)
	select top 0 * into #itemsets8 from #itemsets1
	insert into #itemsets8
		select distinct 'chem_masterOID', CODE,
			case when charindex('--', description) > 0 then
			left(description, charindex('--', description)-1) else  -- Removes the concatinated location in the description field to get name
			description end,
			null, null, null, null, null, null, vm.Inventory_Location, null
		from v_tfm_vt_act_Chem_MasterOID vm
		inner join TFM_ACT_Chemical_Master m
		on vm.CODE = m.ObjectID
		where vm.PropertyOID = @propertyOID and vm.activeflag = 1 and m.GTFF_Approved_IND = 'Y';

	-- Table 9: PLANTING SPECIES
	-- This table should be a list of all active planting species for a given property
	select top 0 * into #itemsets9 from #itemsets1
	insert into #itemsets9
		select distinct 'REG_Species', SPECIES_CODE, SPECIES_DESC, null, null, null, null, 'stand', null, null, null
		from V_TFM_VT_Species_RES
		where PropertyOID = @propertyOID and activeflag = 1;

	-- Table 10: PLANTING VARIETY, PLANTING SPECIES
	-- This table should be a list of all planting varieties (and associeated species)
	select top 0 * into #itemsets10 from #itemsets1
	insert into #itemsets10
		select distinct 'REG_Variety', Variety_Code, Variety_DESC, null, null, null, null, null, null, null, SPECIES_CODE
		from V_TFM_VT_Species_RES
		where PropertyOID = @propertyOID and activeflag = 1;

	-- Result Table: Union together
	select * into #result from #itemsets1
	union
	select * from #itemsets2
	union
	select * from #itemsets3
	union
	select * from #itemsets4
	union
	select * from #itemsets5
	union
	select * from #itemsets6
	union
	select * from #itemsets7
	union
	select * from #itemsets8
	union
	select * from #itemsets9
	union
	select * from #itemsets10

	select * from #result
	order by list_name
	
GO


