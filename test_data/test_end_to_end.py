import pytest
import subprocess 
import os
import pandas

# list of columns we are expecting and will match values on
COLUMNS = ['dayOfYear','year','latitude','longitude','genus','specificEpithet','scientificName','lower_count','upper_count','lower_percent','upper_percent','source','subSource','adjustedNcepReanalysisMonthlyMeanTemp','plantStructurePresenceTypes']
Message = ""

# This script expected to executed from the ppo-data-pipeline root
@pytest.mark.parametrize("project", [ "npn", "pep725", "asu", "neon"]) 
def test_end_to_end(project):
    global Message
    #base_dir = os.path.dirname(__file__)

    # set the project, always preceeded with test_
    project_name = 'test_'+project
    # set the project base dir
    project_base_dir = os.path.join('test_data','projects') 
    # set the project base, based on project name
    project_base = 'test_data'+'.projects.'+project_name #python name reference for dynamic class loading
    # set the project output path
    project_path = os.path.join(project_base_dir,project_name)
    # output directory
    output_path = os.path.join('test_data','data',project_name,'output')
    # input directory
    input_path = os.path.join('test_data','data',project_name,'input')
    # path pointing to onfiguration files. we do not use the main project configuration directory 
    # for the application itself as that may contain changes we don't wish to test.
    # to test changes in configuration files the relevant config files should be copied here
    config_path = os.path.join('test_data','config')
    # reference to ontology. Do NOT change this as it will interfere with rest results. it is Okay if ontology is
    # out of date.  Here we reference a specific release of the ontology itself so it should be static
    #ontology_url = 'https://raw.githubusercontent.com/PlantPhenoOntology/ppo/master/releases/2017-10-20/ppo.owl'
    ontology_url = os.path.join('file:/',config_path,'ppo.owl')
    # file containing actual results we want to compare to
    actual_results_file_name = os.path.join(output_path,"output_reasoned_csv","data_1.ttl.csv")
    # file containing expected results
    expected_results_file_name = os.path.join('test_data','test_'+project+'_results.csv')
    # name of file to store output text, if test fails we can learn more information in this file
    output_file = 'output.txt'

    # The ontology is hard-coded here so tests can pass even if ontology is changed.
    # The presence here of an up to data ontology is not necessary since we're just 
    # performing tests on pipeline functionality
    cmd = ['python', './process.py', project_name, output_path, '--input_dir', input_path,'--config_dir',config_path,'--ontology',ontology_url,'--base_dir',project_path,'--project_base',project_base ]

    # setup process to execute given command
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("")
    print("the commandline is")
    print(subprocess.list2cmdline(cmd))


    # output reresults from process
    
    stdout, stderr = proc.communicate()
    out = open(output_file,'wb')
    out.write(stdout)
    out.close() 
    err = open(output_file+ '.err','wb')
    err.write(stderr)
    err.close() 

    # wait for process to complete before continuing
    p_status = proc.wait()

    # Simple test to make sure the program exited with a good status
    assert p_status==0
    
    # Read actual results, stored as results_file into an array of lines
    assert True == os.path.exists(actual_results_file_name)
    actual_results_df = pandas.read_csv(actual_results_file_name,sep=",")
    actual_results_df = actual_results_df.drop(actual_results_df.columns[0], axis=1)
    actual_results=[]

    for row in actual_results_df.iterrows():
        index, data = row
        actual_results.append(data)

    # Read expected results, stored as results_file into an array of lines
    assert True == os.path.exists(expected_results_file_name)
    expected_results = pandas.read_csv(expected_results_file_name,sep=",")
    expected_results = expected_results.drop(expected_results.columns[0], axis=1)

    # loop expected results and search for matching lines in output
    for index, e_line in expected_results.iterrows():
        foundMatch = False
        Message = ""
        # loop actual output lines
        for a_line in actual_results:
            # search for the expected line in the output, by looking at each row
            if rows_match(e_line,a_line):
                foundMatch = True
        if (foundMatch):
            assert True
        else:
            assert False, Message

    # we should see the same number for results in output file as
    # the expected, with the exception of the header line
    #assert len(expected_results) == len(actual_results)-1, "mismatched number of lines"

# Compare each value in each row
# 1. we do not specify the eventID column, since these are often UUIDs generated by the load where
# clients don't have their own stable ID
# 2. we handle plantStructurePresenceTypes specially, irrespective of the order they appear in
def rows_match(e_line,a_line):
    global Message
    count = 0
    try:
        while count < len(COLUMNS):
            #check for plantstructurepresencetypes in any order
            if (COLUMNS[count] == 'plantStructurePresenceTypes'):
                actualPSP = a_line['plantStructurePresenceTypes'].split("|")
                expectedPSP = e_line['plantStructurePresenceTypes'].split("|")
                pspCount = 0
                for e in expectedPSP:
                    if e not in actualPSP:
                        if (Message == ""):
                            Message = "Did not find expected plant structure presence type in actual results " + e
                        count = 9999
                count = count + 1
            #check for matching column value
            elif str(a_line[COLUMNS[count]]) == str(e_line[COLUMNS[count]]):
                count = count + 1
            else:
                if (Message == ""):
                    Message = "Did not find expected value " + str(e_line[COLUMNS[count]]) + " in column " + str(COLUMNS[count])
                count = 9999
    except (KeyError) as err:
        assert False, "missing column: " + COLUMNS[count]

    if (count < 9999):
        return True
    else:
        return False

