"""
Evaluate all implemented estimators and print results.
For development and testing.
"""

import os
from chemMAP.carcino_CV_score import carcino_CV_score
from chemMAP.CarcinogenesisOWLparser import load_ontology
from chemMAP.LearningProblemParser import get_learning_problems
from chemMAP.transformers.utils import filter_compounds, filter_bonds, filter_structs, filter_atoms
from pprint import pprint
from pathlib import Path
from chemMAP.estimators.DecisionTreeBond import DecisionTreeBond
from chemMAP.estimators.DecisionTreeAtom import DecisionTreeAtom
from chemMAP.estimators.DecisionTreeStruct import DecisionTreeStruct
from chemMAP.estimators.DecisionTreeCompound import DecisionTreeCompound
from chemMAP.estimators.DecisionTreeAll import DecisionTreeAll

verbose = True
result_folder = Path("results")
estimator_list = [DecisionTreeAll]
data_filter = None  # filter_compounds, filter_bonds, filter_structs, filter_atoms, None for all data

if __name__ == "__main__":

    if verbose:
        log = print
    else:
        log = lambda x:False
    
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)
 
    log("loading ontology...")
    ontology = load_ontology()

    log("loading learning problems...")
    # learning_problems = get_learning_problems(source="data/kg-mini-project-grading.ttl")
    learning_problems = get_learning_problems(source="data/kg-mini-project-train_v2.ttl")
    # learning_problems = get_learning_problems(source="data/kg-mini-project-train.ttl")

    log("starting evaluation")
    mean_results = {}
    for i, estimator_cls in enumerate(estimator_list):
        class_name = str(estimator_cls).split("'")[1].split(".")[-1]
        log(f"evaluating {class_name}, {i+1}/{len(estimator_list)}")
        estimator_results = {}
        for i, lp in enumerate(learning_problems):
            lp_name = lp["name"]
            log(f"learning problem {lp_name}, {i+1}/{len(learning_problems)}")
            estimator = estimator_cls(ontology)
            if data_filter is not None:
                examples, labels = data_filter(ontology, lp["examples"], lp["labels"])
            else:
                examples, labels = lp["examples"], lp["labels"]
            included = sum(labels)
            excluded = len(labels) - included
            if included == 0 or excluded == 0:
                log("Learning Problem is trivial, skipping...")
                continue
            log(f"Number of examples: {len(labels)}, {included} included and {excluded} excluded.")
            log("Starting cross-validation...")
            lp_result = carcino_CV_score(estimator, examples, labels)
            pprint(lp_result)
            log("Finished cross-validation.")
            estimator_results[lp_name] = lp_result
        
        mean_result = {}
        measure_count = {}
        for lp_result in estimator_results.values():
            for measure, value in lp_result.items():
                if measure not in mean_result:
                    mean_result[measure] = value
                else:
                    mean_result[measure] += value
                if measure not in measure_count:
                    measure_count[measure] = 0
                measure_count[measure] += 1
        
        for measure in mean_result:
            mean_result[measure] /= measure_count[measure]
        
        with open(result_folder/(class_name+".dat"), "w") as f:
            pprint(estimator_results, stream=f)
        mean_results[estimator_cls] = mean_result

    log("writing results to file...")
    with open(result_folder/"mean_results.dat", "w") as f:
       pprint(mean_results, stream=f)
    pprint(mean_results)
