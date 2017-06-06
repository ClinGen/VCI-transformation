import sys
from collections import defaultdict
import requests
import hashlib
import csv
from interpretation_generated import *
from interpretation_extras import *
from interpretation_constants import *
from Allele import Variant

IRI_BASE='https://vci.clinicalgenome.org'
VCI_ID_KEY = '@id'
VCI_TYPE_KEY = '@type'
VCI_CONTRIBUTION_KEY = 'submitted_by'
VCI_LAST_MODIFIED_KEY = 'last_modified'
VCI_AGENT_NAME_KEY = 'title'
VCI_AUTOCLASSIFICATION_KEY = 'autoClassification'
VCI_VARIANT_KEY = 'variant'
VCI_VARIANT_TYPE = 'variant'
VCI_ORPHA_TYPE = 'orphaPhenotype'
VCI_AGENT_TYPE = 'user'
VCI_CANONICAL_ID_KEY = 'carId'
VCI_HGVS_NAMES_KEY = 'hgvsNames'
VCI_GENOMIC_HGVS_38_KEY = 'GRCh38'
VCI_CONDITION_KEY = 'disease'
VCI_TERM_KEY = 'term'
VCI_ORPHA_KEY = 'orphaNumber'
VCI_EVALUATION_KEY = 'evaluations'
VCI_EVALUATION_VARIANT_KEY = 'variant'
VCI_CRITERIA_KEY = 'criteria'
VCI_CRITERIA_STATUS_KEY = 'criteriaStatus'
VCI_CRITERIA_NOT_EVALUATED = 'not-evaluated'
VCI_MET = 'met'
VCI_NOT_MET = 'not-met'
VCI_EVALUATION_EXPLANATION_KEY = 'explanation'
VCI_EVIDENCE_DESCRIPTION_KEY = 'evidenceDescription'
VCI_CRITERIA_MODIFIER_KEY = 'criteriaModifier'
VCI_MODIFIER_KEY = 'modifier'
VCI_FREQUENCY_KEY = 'population'
VCI_POPULATION_DATA_KEY = 'populationData'
VCI_COMPUTATIONAL_KEY = 'computational'
VCI_COMPUTATIONAL_DATA_KEY = 'computationalData'
VCI_COMPUTATIONAL_ALLELE_KEY = 'variant'
VCI_CLINGEN_COMPUTATION_KEY = 'clingen'
VCI_OTHER_COMPUTATION_KEY = 'other_predictors'
VCI_CONSERVATION_KEY = 'conservation'
VCI_CONSERVATION_DATA_KEY = 'conservationData'
VCI_ESP_KEY = 'esp'
VCI_EXAC_KEY = 'exac'
VCI_1000_GENOMES_KEY = 'tGenomes'
VCI_FREQUENCY_ALLELE_KEY='_extra'
VCI_COMBINED_POP = '_tot'
VCI_EUROPEAN_AMERICAN_POP = 'ea'
VCI_AFRICAN_AMERICAN_POP = 'aa'
VCI_CHROMOSOME_KEY = 'chrom'
VCI_REF_ALLELE_KEY = 'ref'
VCI_ALT_ALLELE_KEY = 'alt'
VCI_HG19_START_KEY = 'hg19_start'
VCI_EXAC_START_KEY = 'pos'
VCI_ALLELE_COUNT_KEY = 'ac'
VCI_ALLELE_NUMBER_KEY = 'an'
VCI_ALLELE_FREQUENCY_KEY = 'af'
VCI_GENOTYPE_COUNT_KEY = 'gc'
VCI_EXAC_AFRICAN = 'afr'
VCI_EXAC_LATINO_POP = 'amr'
VCI_EXAC_EAST_ASIAN_POP = 'eas'
VCI_EXAC_FINNISH_POP = 'fin'
VCI_EXAC_NON_FINNISH_EURO_POP = 'nfe'
VCI_EXAC_SOUTH_ASIAN_POP = 'sas'
VCI_EXAC_OTHER_POP = 'oth'
VCI_HOMOZYGOUS_GENOTYPE_COUNT_KEY = 'hom'
VCI_1000_GENOMES_DBSNP_KEY = 'name'
VCI_1000_GENOMES_AFRICAN_POP = 'afr'
VCI_1000_GENOMES_LATINO_POP = 'amr'
VCI_1000_GENOMES_EAST_ASIAN_POP = 'eas'
VCI_1000_GENOMES_SOUTH_ASIAN_POP = 'sas'
VCI_1000_GENOMES_EURO_POP = 'eur'
VCI_1000_GENOMES_ESP_AA_POP = 'espaa'
VCI_1000_GENOMES_ESP_EA_POP = 'espea'
VCI_SCORE_KEY = 'score'
VCI_PREDICTION_KEY = 'prediction'
VCI_EXTRA_EVIDENCE_KEY = 'extra_evidence_list'
VCI_ARTICLES_KEY = 'articles'
VCI_PMID_KEY = 'pmid'
VCI_CATEGORY_KEY = 'category'
VCI_SUBCATEGORY_KEY = 'subcategory'

VCI_MISSENSE_EFFECT_PREDICTOR = 'missense_predictor'
VCI_SPLICE_EFFECT_PREDICTOR = 'splice'

#TEMP FIX UNTIL ALLELE_FREQ.ascertainment is made a CodeableConcept
DMWG_ESP='ESP'
DMWG_1KGESP='1KG_ESP'
DMWG_1KG='1KG'
DMWG_EXAC='ExAC'

term_map = { VCI_MET: 'http://clinicalgenome.org/datamodel/criterion-assertion-outcome/met', \
             VCI_NOT_MET: 'http://clinicalgenome.org/datamodel/criterion-assertion-outcome/not-met', \
             VCI_MISSENSE_EFFECT_PREDICTOR: 'http://clinicalgenome.org/datamodel/prediction-type/me', \
             VCI_SPLICE_EFFECT_PREDICTOR: 'http://clinicalgenome.org/datamodel/prediction-type/sp' \
             }

extra_evidence_map = { ('population','population'): ['BA1','PM2','BS1'],\
                       ('predictors','functional-conservation-splicing-predictors'): ['PP3','BP4','BP1','PP2'], \
                       ('predictors','other-variants-in-codon'): ['PM5','PS1'], \
                       ('predictors','null-variant-analysis'): ['PVS1'], \
                       ('predictors','molecular-consequence-silent-intron'): ['BP7'], \
                       ('predictors','molecular-consequence-inframe-indel'): ['BP3','PM4'], \
                       ('experimental','hotspot-functional-domain'): ['PM1'], \
                       ('experimental','experimental-studies'): ['BS3','PS3'], \
                       ('case-segregation','observed-in-healthy'): ['BS2'], \
                       ('case-segregation','case-control'): ['PS4'], \
                       ('case-segregation','segregation-data'): ['BS4','PP1'], \
                       ('case-segregation','de-novo'): ['PM6','PS2'], \
                       ('case-segregation','allele-data'): ['BP2','PM3'], \
                       ('case-segregation','alternate-mechanism'): ['BP5'], \
                       ('case-segregation','specificity-of-phenotype'): ['PP4'], \
                       ('case-segregation','reputable-source'): ['BP6','PP5'] }

def get_chromosome_name(chromosome, version):
    v37chromosomes={'1':'NC_000001.10',\
                    '2':'NC_000002.11',\
                    '3':'NC_000003.11',\
                    '4':'NC_000004.11',\
                    '5':'NC_000005.9',\
                    '6':'NC_000006.11',\
                    '7':'NC_000007.13',\
                    '8':'NC_000008.10',\
                    '9':'NC_000009.11',\
                    '10':'NC_000010.10',\
                    '11':'NC_000011.9',\
                    '12':'NC_000012.11',\
                    '13':'NC_000013.10',\
                    '14':'NC_000014.8',\
                    '15':'NC_000015.9',\
                    '16':'NC_000016.9',\
                    '17':'NC_000017.10',\
                    '18':'NC_000018.9',\
                    '19':'NC_000019.9',\
                    '20':'NC_000020.10',\
                    '21':'NC_000021.8',\
                    '22':'NC_000022.10',\
                    'X':'NC_000023.10',\
                    'Y':'NC_000024.9',\
                    'M':'NC_012920.1'}
    if version in ( 'hg19', 'GRCh37' ):
        return v37chromosomes[ str(chromosome) ]
    else:
        raise Exception

def get_canonical_id(hgvs):
    # send a GET request with parameter
    url = 'http://reg.genome.network/allele?hgvs='
    # convert symbol > to special code %3E
    url += requests.utils.quote(hgvs)
    res = requests.get(url)
    txt = res.text
    cardata = json.loads(txt)
    return cardata

#We don't need to entity map everything, just some of the data nodes.
# For instance, not the interpretation.  When it occurs multiple times, 
# it causes problems because the evaluations at each level
# are represented differently.
class EntityMap:
    EMtypes = set([VCI_VARIANT_TYPE, VCI_AGENT_TYPE, VCI_ORPHA_TYPE])
    def __init__(self, source, idtag='@id'):
        self.entities = defaultdict(dict)
        self.transformed={}
        self.idtag = idtag
        self.walk(source)
    def walk(self,source):
        if isinstance(source,list):
            for e in source:
                self.walk(e)
        elif isinstance(source,dict):
            self.register(source)
            for k,v in source.items():
                self.walk(v)
        else:
            pass
    def register(self,node):
        if self.idtag in node:
            if len(self.EMtypes.intersection(set(node[VCI_TYPE_KEY]))) != 0:
                atid = fully_qualify(node[self.idtag])
                entity = self.entities[atid]
                for key in node:
                    if key in entity:
                        if entity[key] != node[key]:
                            print key, '\n--------\n',entity[key], '\n---------------\n',node[key]
                            raise Exception('Incoherent Nodes')
                    else:
                        entity[key] = node[key]
                #print atid,entity
    def get_entity(self,eid):
        return self.entities[eid]
    def get_transformed(self,eid):
        if eid in self.transformed:
            return self.transformed[eid]
        return None
    def add_transformed(self,eid,entity):
        self.transformed[eid] = entity
        
def canonicalizeVariant(rep):
    orig_carid = rep[VCI_CANONICAL_ID_KEY]
    #We want to get the id/representation from the Baylor Allele Registry.
    hgvs38 = rep[VCI_HGVS_NAMES_KEY][VCI_GENOMIC_HGVS_38_KEY]
    baylor_car_rep = get_canonical_id(hgvs38)
    baylor_carid = baylor_car_rep['@id']
    #Make sure it's the same id
    if (orig_carid != '') and (orig_carid != baylor_carid):
        print orig_carid
        print baylor_carid
        raise Exception
    return baylor_car_rep 

def fully_qualify(iri):
    fqiri = iri
    if fqiri.startswith('/'):
        fqiri = IRI_BASE + fqiri
    return fqiri

def get_id(source):
    if isinstance(source, dict):
        sid = fully_qualify(source[VCI_ID_KEY])
    else:
        sid = fully_qualify(source)
    return sid


def add_contribution( user_input, target, ondate, entities, role ):
    userid = get_id(user_input)
    user = entities.get_entity(userid)
    #print 'User:',user
    agent = entities.get_transformed(userid)
    if agent is None:
        agent = Agent(userid)
        try:
            agent.set_name( user[VCI_AGENT_NAME_KEY] )
        except KeyError:
            #sometimes we might not have the name.. oh well.
            pass
        entities.add_transformed(userid, agent)
    #contribution = Contribution(agent, ondate, role)
    contribution = create_contribution(agent, ondate, role)
    target.add_contribution(contribution)

def add_contributions( source, target, entities, ondate, role ):
    if isinstance( source, list ):
        for single_source in source:
            add_contribution( single_source, target, ondate, entities, role)
    else:
        add_contribution( source, target,  ondate, entities, role)

#Ignore these keys:
# interpretation_genes: unused in the VCI
# actions: tracking user behavior
# markAsProvisional: UI/process related
# submitted_by: this is who started the interpretion.  we care who ended it. (in prov_variant)
# uuid: redundant with @id
# schema_version: not relevant to transformed interp
# evaluation_count: we can figure out from the list of evaluations
# status: not tracking status
# interpretation_status
# last_modified: using the information from the provisional_variant
# audit: Interal information
# interpretation disease: redundant with disease
# date created: Not tracking user behavior
# provisional_count: should be 1:1
#Still need to handle:
# modeInheritanceAdjective: for things like "with maternal imprinting"
# extra_evidence_list
def transform_root(vci):
    return VariantInterpretation( fully_qualify(vci[VCI_ID_KEY]) )
    #Is there a place where explanation should come from?
    #dmwg['explanation'] = 

#Ignore:
# status: not tracking status
# uuid: redudant with id
# @id: we don't need an id for this entity which we are merging with the parent
#  Confirmed with Karen on 4/19/2017 that the id for tracking submission is the interpretation id.
# interpretation_associated: just a reverse link to the parent
# schema_version: not relevant to the transformed interpretation
# date_create: just tracking end dates
#May need to handle
# alteredClassification_present
# reason_present
def transform_provisional_variant(vci_pv , interpretation, entities ):
    if isinstance(vci_pv, list):
        if len(vci_pv) > 1:
            print '???'
            exit()
        vci_pv = vci_pv[0]
    add_contributions( vci_pv[VCI_CONTRIBUTION_KEY], interpretation, entities, vci_pv[VCI_LAST_MODIFIED_KEY], DMWG_INTERPRETER_ROLE ,)
    interpretation.set_clinicalSignificance( convert_significance(vci_pv) )

def convert_significance(vci_provisional_variant):
    value = vci_provisional_variant[VCI_AUTOCLASSIFICATION_KEY]
    return value

#TODO: how do we want to format variants?
def transform_variant(variant,entities):
    vci_variant_id = get_id(variant)
    dmwg_variant = entities.get_transformed(vci_variant_id)
    if dmwg_variant is None:
        vci_variant = entities.get_entity(vci_variant_id)
        ar_variant = canonicalizeVariant( vci_variant )
        dmwg_variant = Variant(ar_variant)
        entities.add_transformed(vci_variant_id, dmwg_variant)
    return dmwg_variant

#Evaluation keys:
## Ones we won't use
# date_created
# schema_version
# interpretation_associated
# uuid
# @type
# status
# evidence_type: going to be clear from the data
## Go into contribution
# last_modified X
# submitted_by X
## Identifier X
# @id
## transform
# criteria X
# criteriaStatus X
# explanation X
# criteriaModifier  THIS IS STILL IN PROGRESS UNTIL THE JSON GETS CLEARED UP
# modifier: related to criteriaModifier for the UI
# variant X
# population: this is actually allele frequency data (in populations, not a population itself)
#TODO: don't we need to handle condition in the evaluations too?
#TODO: CRITERION IS PROBABLY NOT GOING TO HAVE ALL THIS DETAIL
def transform_evaluation(vci_evaluation, interpretation, entities, criteria):
    dmwg_assessment = CriterionAssessment( vci_evaluation[VCI_ID_KEY] )
    criterion = criteria[ vci_evaluation[ VCI_CRITERIA_KEY] ]
    dmwg_assessment.set_criterion( criterion )
    dmwg_assessment.set_outcome( term_map[ vci_evaluation[ VCI_CRITERIA_STATUS_KEY ] ] )
    dmwg_assessment.set_explanation( vci_evaluation[ VCI_EVALUATION_EXPLANATION_KEY] )
    dmwg_assessment.set_variant( transform_variant( vci_evaluation[VCI_EVALUATION_VARIANT_KEY ] , entities) )
    #Have to do a little work to figure out the strength
    #VCI has both a modifier and a criteria modifier.  If these both exist they should be the
    #same, but if one or the other does not exist, then we should use the other one.
    crit_mod = ''
    mod = ''
    if VCI_CRITERIA_MODIFIER_KEY in vci_evaluation:
        crit_mod = vci_evaluation[VCI_CRITERIA_MODIFIER_KEY]
    if VCI_MODIFIER_KEY in vci_evaluation:
        mod = vci_evaluation[VCI_MODIFIER_KEY]
    if crit_mod != mod:
        raise Exception
    defaultStrength = criterion.get_defaultStrength()
    strength = transform_strength( crit_mod, defaultStrength )
    ##TODO: Also add contribution to the evidence line if crit_mod != ''.  A little tricky since I hid the evidence line, but it's gettable 
    add_contributions( vci_evaluation[VCI_CONTRIBUTION_KEY], dmwg_assessment, entities,vci_evaluation['last_modified'], DMWG_ASSESSOR_ROLE)
    #Now the evidence
    if VCI_FREQUENCY_KEY in vci_evaluation:
        frequencies = transform_frequency( vci_evaluation[VCI_FREQUENCY_KEY],  entities)
        add_informations( dmwg_assessment, frequencies )
    if VCI_COMPUTATIONAL_KEY in vci_evaluation:
        predictions = transform_computational( vci_evaluation[VCI_COMPUTATIONAL_KEY], entities )
        add_informations( dmwg_assessment, predictions )
    add_criterion_assessment(interpretation, dmwg_assessment, strength)
    return vci_evaluation[VCI_CRITERIA_KEY], dmwg_assessment

def transform_computational(source, entities):
    predictions = []
    vci_variant = source[VCI_VARIANT_KEY]
    #the form of this call suggests that the transform* functions should be member functions of entitymap
    dmwg_variant = transform_variant(vci_variant,entities) 
    compdata = source[VCI_COMPUTATIONAL_DATA_KEY]
    if VCI_CONSERVATION_KEY in compdata:
        predictions += transform_conservation_data( compdata[VCI_CONSERVATION_KEY] , dmwg_variant )
    if VCI_CLINGEN_COMPUTATION_KEY in compdata:
        predictions += transform_clingen_comp_data( compdata[VCI_CLINGEN_COMPUTATION_KEY], dmwg_variant )
    if VCI_OTHER_COMPUTATION_KEY in compdata:
        predictions += transform_other_comp_data( compdata[VCI_OTHER_COMPUTATION_KEY], dmwg_variant )
    add_contributions_to_data( source , predictions, entities )
    return predictions 

def transform_clingen_comp_data( source,variant):
    predictions = []
    for pred in source:
        score = source[pred][VCI_SCORE_KEY]
        #Have to sort out the scores....
        if score is not None:
            dmwg_prediction = InSilicoPrediction()
            #We really also want to set the transcript, but the VCI is not returning that informaiton
            #dmwg_prediction.set_transcript()
            dmwg_prediction.set_canonicalAllele(variant)
            dmwg_prediction.set_algorithm(pred)
            dmwg_prediction.set_quantitativePrediction(score)
            dmwg_prediction.set_predictionType( term_map[VCI_MISSENSE_EFFECT_PREDICTOR] )
            predictions.append(dmwg_prediction)
    return predictions

def transform_other_comp_data( source, variant ):
    predictions = []
    for pred in source:
        scores = source[pred][ VCI_SCORE_KEY ]
        predsv  = source[pred][ VCI_PREDICTION_KEY ]
        if (scores is not None) and (not isinstance(scores, list)):
            scores = [ scores ]
        if scores is not None and predsv is not None:
            preds  = predsv.split(',')
        elif scores is None and predsv is not None:
            preds = predsv.split(',')
            scores = [ None for p in preds ]
        elif scores is not None and predsv is None:
            preds = [None for s in scores]
        else:
            #both none, ignore
            continue
        for (s,p) in zip(scores,preds):
            dmwg_prediction = InSilicoPrediction()
            dmwg_prediction.set_predictionType( term_map[ VCI_MISSENSE_EFFECT_PREDICTOR]  )
            dmwg_prediction.set_canonicalAllele( variant )
            dmwg_prediction.set_algorithm( pred )
            if s is not None:
                dmwg_prediction.set_quantitativePrediction(s)
            if p is not None:
                dmwg_prediction.set_categoricalPrediction(p)
        predictions.append(dmwg_prediction)
    return predictions


#The values from VCI are not including a true/false on whether the thing is conserved. But we'll want that.
def transform_conservation_data( source, variant ):
    results = []
    for constool in source:
        dmwg_conservation = Conservation()
        dmwg_conservation.set_allele(variant)
        dmwg_conservation.set_algorithm(constool)
        dmwg_conservation.set_score(source[constool])
        results.append(dmwg_conservation)
    return results

def transform_frequency( source, entities):
    popdata    = source[VCI_POPULATION_DATA_KEY]
    vci_variant = source[VCI_VARIANT_KEY]
    #the form of this call suggests that the transform* functions should be member functions of entitymap
    dmwg_variant = transform_variant(vci_variant,entities) 
    frequencies = []
    if VCI_ESP_KEY in popdata:
        esp_frequencies = transform_esp_data( popdata[VCI_ESP_KEY],  dmwg_variant )
        frequencies += esp_frequencies
    if VCI_EXAC_KEY in popdata:
        exac_frequencies = transform_exac_data( popdata[VCI_EXAC_KEY], dmwg_variant )
        frequencies += exac_frequencies
    if VCI_1000_GENOMES_KEY in popdata:
        tg_frequencies = transform_1000_genomes_data(popdata[VCI_1000_GENOMES_KEY], dmwg_variant)
        frequencies += tg_frequencies
    #Add contributors to data nodes
    add_contributions_to_data( source , frequencies, entities )
    return frequencies

def add_contributions_to_data( data_source, data_targets, entities):
    submitters = data_source[VCI_CONTRIBUTION_KEY]
    modtime    = data_source[VCI_LAST_MODIFIED_KEY]
    for data in data_targets:
        add_contributions( submitters, data, entities, modtime, DMWG_CURATOR_ROLE)


#Clean up the VCI keys and decide if they are per experiment or not.
def convert_esp_pop(pop):
    if pop == VCI_COMBINED_POP:
        return 'combined'
    return 'http://evs.gs.washington.edu/EVS/%s' % pop

def convert_exac_pop(pop):
    if pop == VCI_COMBINED_POP: return 'combined'
    if pop == VCI_EXAC_OTHER_POP: return 'other'
    return 'http://broadinstitute.org/populations/%s' % pop

def convert_1000_genomes_pop(pop):
    if pop == VCI_COMBINED_POP: return 'combined'
    if pop in [ VCI_1000_GENOMES_ESP_AA_POP, VCI_1000_GENOMES_ESP_EA_POP ]:
        return 'http://evs.gs.washington.edu/EVS/%s' % pop[-2:].upper()
    return 'http://www.internationalgenome.org/category/population/%s' % pop

def transform_1000_genomes_data( source, dmwg_variant ):
    alt_allele = dmwg_variant.get_allele('GRCh37') #right?
    frequencies = []
    for pop in source:
        if pop != VCI_FREQUENCY_ALLELE_KEY:
            if pop in [VCI_1000_GENOMES_ESP_EA_POP, VCI_1000_GENOMES_ESP_AA_POP]:
                dmwg_af = AlleleFrequency()
                dmwg_af.set_ascertainment(DMWG_1KGESP)
            else:
                dmwg_af = AlleleFrequency()
                dmwg_af.set_ascertainment(DMWG_1KG)
            frequencies.append(dmwg_af)
            dmwg_af.set_allele( dmwg_variant )
            dmwg_af.set_population(  convert_1000_genomes_pop(pop) )
            if len( source[pop][VCI_ALLELE_COUNT_KEY] ) == 0:
                dmwg_af.set_alleleNumber( 0 )
            else:
                dmwg_af.set_alleleNumber( sum( source[pop][VCI_ALLELE_COUNT_KEY].values() ) )
            #TODO: Should the element be not here, or should it be 0 or should it be null?
            if dmwg_af.get_alleleNumber() > 0:
                if alt_allele in source[pop][VCI_ALLELE_FREQUENCY_KEY]:
                    dmwg_af.set_alleleFrequency( source[pop][VCI_ALLELE_FREQUENCY_KEY][alt_allele] )
                else:
                    dmwg_af.set_alleleFrequency( 0.  )
            if alt_allele in source[pop][VCI_ALLELE_COUNT_KEY]:
                dmwg_af.set_alleleCount( source[pop][VCI_ALLELE_COUNT_KEY][alt_allele] )
            else:
                dmwg_af.set_alleleCount( 0 )
            hkey = '%s|%s' % (alt_allele,alt_allele)
            if hkey in source[pop][VCI_GENOTYPE_COUNT_KEY]:
                dmwg_af.set_homozygousAlleleIndividualCount(  source[pop][VCI_GENOTYPE_COUNT_KEY][hkey] )
            else:
                dmwg_af.set_homozygousAlleleIndividualCount( 0 )
    return frequencies


def transform_exac_data( source, dmwg_variant ): 
    frequencies = []
    for pop in source:
        if pop != VCI_FREQUENCY_ALLELE_KEY:
            dmwg_af = AlleleFrequency()
            dmwg_af.set_ascertainment(DMWG_EXAC)
            frequencies.append(dmwg_af)
            dmwg_af.set_population( convert_exac_pop(pop) )
            dmwg_af.set_allele( dmwg_variant )
            if VCI_ALLELE_COUNT_KEY in source[pop]:
                dmwg_af.set_alleleCount(  source[pop][VCI_ALLELE_COUNT_KEY] )
            else:
                dmwg_af.set_alleleCount( 0 )
            if VCI_ALLELE_NUMBER_KEY in source[pop]:
                dmwg_af.set_alleleNumber(source[pop][VCI_ALLELE_NUMBER_KEY])
            else:
                dmwg_af.set_alleleNumber(0)
            if dmwg_af.get_alleleNumber() > 0:
                dmwg_af.set_alleleFrequency(source[pop][VCI_ALLELE_FREQUENCY_KEY])
            if VCI_HOMOZYGOUS_GENOTYPE_COUNT_KEY in source[pop]:
                dmwg_af.set_homozygousAlleleIndividualCount( source[pop][VCI_HOMOZYGOUS_GENOTYPE_COUNT_KEY] )
            else:
                dmwg_af.set_homozygousAlleleIndividualCount( 0 )
    return frequencies
            

def transform_esp_data(source,dmwg_variant):
    ref_allele = dmwg_variant.get_ref_allele('GRCh37')
    alt_allele = dmwg_variant.get_allele('GRCh37')
    frequencies = []
    for pop in source:
        if pop != VCI_FREQUENCY_ALLELE_KEY:
            dmwg_af = AlleleFrequency( )
            dmwg_af.set_ascertainment(DMWG_ESP)
            frequencies.append(dmwg_af)
            dmwg_af.set_population( convert_esp_pop(pop) )
            dmwg_af.set_allele( dmwg_variant )
            #Assumes ESP uses v37
            if (len(source[pop][VCI_ALLELE_COUNT_KEY]) > 0) and (alt_allele in source[pop][VCI_ALLELE_COUNT_KEY]):
                dmwg_af.set_alleleCount( source[pop][VCI_ALLELE_COUNT_KEY][alt_allele] )
            else:
                dmwg_af.set_alleleCount( 0 )
            dmwg_af.set_alleleNumber( sum(source[pop][VCI_ALLELE_COUNT_KEY].values()) )
            if dmwg_af.get_alleleNumber() > 0:
                f = 1.*dmwg_af.get_alleleCount() / dmwg_af.get_alleleNumber()
                dmwg_af.set_alleleFrequency(f)
            if len(source[pop][VCI_GENOTYPE_COUNT_KEY]) > 0:
                homkey = '%s%s' % (alt_allele,alt_allele)
                dmwg_af.set_homozygousAlleleIndividualCount(source[pop][VCI_GENOTYPE_COUNT_KEY][homkey])
                hetkey1 = '%s%s' % (ref_allele,alt_allele)
                hetkey2 = '%s%s' % (alt_allele,ref_allele)
                if hetkey1 in  source[pop][VCI_GENOTYPE_COUNT_KEY]:
                    dmwg_af.set_heterozygousAlleleIndividualCount(source[pop][VCI_GENOTYPE_COUNT_KEY][hetkey1])
                elif hetkey2 in  source[pop][VCI_GENOTYPE_COUNT_KEY]:
                    dmwg_af.set_heterozygousAlleleIndividualCount( source[pop][VCI_GENOTYPE_COUNT_KEY][hetkey2] )
    f = frequencies[0]
    return frequencies


#shitty code here, depends on some hard coding for strength.
#should read the codings from an external source
def transform_strength(modifier, defaultStrength):
    if modifier == '':
        return defaultStrength
    if modifier == 'strong':
        mod = 's'
    elif modifier == 'supporting':
        mod = 'p'
    elif modifier == 'moderate':
        mod = 'm'
    strength = defaultStrength.get_coding()[0].get_id()[:-1] + mod
    return strength

#Returns a dictionary that maps from criterion id (e.g. "PS2") to 
# a dmwg assessment entity
def transform_evaluations(evaluation_list,interpretation,entities):
    evaluation_map = {}
    criteria = read_criteria()
    if not isinstance(evaluation_list, list):
        raise Exception
    for vci_eval in evaluation_list:
        if vci_eval[ VCI_CRITERIA_STATUS_KEY ] == VCI_CRITERIA_NOT_EVALUATED:
                continue
        crit_id, evaluation = transform_evaluation(vci_eval,interpretation,entities,criteria)
        evaluation_map[crit_id] = evaluation
    return evaluation_map

def transform_articles( article_list, interpretation, entities ):
    sourcelist = []
    for article in article_list:
        pmid = article[ VCI_PMID_KEY ]
        atid = 'https://www.ncbi.nlm.nih.gov/pubmed/%s' % pmid
        isource = InformationSource(atid)
        sourcelist.append(isource)
    return sourcelist

# The evidence in the VCI is not a child node of the evaluation.  It is linked to the relevant 
# rules via the category and subcategory proerties
def transform_evidence(extra_evidence_list, interpretation, entities, evalmap):
    for ee_node in extra_evidence_list:
        info = Information()
        add_contributions_to_data( ee_node, [info], entities )
        info.set_explanation( ee_node[ VCI_EVIDENCE_DESCRIPTION_KEY] )
        sources = transform_articles(ee_node[ VCI_ARTICLES_KEY], interpretation, entities )
        for source in sources:
            info.add_source(source)
        key = ( ee_node[VCI_CATEGORY_KEY], ee_node[ VCI_SUBCATEGORY_KEY] )
        possible_rules = extra_evidence_map[key]
        found = False
        for rule in possible_rules:
            if rule in evalmap:
                found = True
                dmwg_assessment = evalmap[rule]
                add_informations( dmwg_assessment, [info])
        if not found:
            print  "Did not find any evaluated criteria for this data: %s "% ee_node['uuid']


#VCI brings in ORPHANET only conditions.  If this is not the case, this will require rework
#Note that we don't necessarily have the full VCI disease node when we get into this function.  
# It could be anything from a bare IRI to a full node or anything in between.  The first two lines
# standardize the "local" information to the "global" information node.
def transform_condition(vci_local_disease,interpretation,entities):
    vci_disease_id = get_id(vci_local_disease)
    vci_disease = entities.get_entity(vci_disease_id)
    dmwg_disease = entities.get_transformed(vci_disease_id)
    if dmwg_disease is None:
        orpha_code = vci_disease[VCI_ORPHA_KEY]
        orpha_name = vci_disease[VCI_TERM_KEY]
        dmwg_disease = create_orphanet_disease(orpha_code, orpha_name)
        entities.add_transformed(vci_disease_id, dmwg_disease)
    dmwg_condition = MendelianCondition()
    dmwg_condition.add_disease(dmwg_disease)
    interpretation.add_condition(dmwg_condition)
 
def transform(jsonf):
    vci = json.load(jsonf)
    entities = EntityMap(vci)
    interpretation = transform_root(vci)
    transform_provisional_variant(vci['provisional_variant'],interpretation,entities)
    variant = transform_variant(vci[VCI_VARIANT_KEY],entities)
    interpretation.set_variant(variant)
    transform_condition(vci[VCI_CONDITION_KEY], interpretation, entities)
    eval_map = transform_evaluations(vci[VCI_EVALUATION_KEY], interpretation, entities)
    transform_evidence(vci[VCI_EXTRA_EVIDENCE_KEY], interpretation, entities, eval_map)
    return interpretation

def transform_json_file(infilename,outfilename):
    inf = file(infilename,'r')
    interp = transform(inf)
    inf.close()
    outf = file(outfilename,'w')
    json.dump(interp,outf,sort_keys=True, indent=4, separators=(',', ': '), cls=InterpretationEncoder)
    outf.close()

def test():
    transform_json_file('test_data/test_interp_1.vci.json', 'test_data/test_interp_1.dmwg.json')

#TODO: add some decent parameter processing.
if __name__ == '__main__':
    transform_json_file(sys.argv[1],sys.argv[2])
