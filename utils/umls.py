import requests
import os
from threading import Thread
import queue
import yaml
# with open("config.yaml", "r") as stream:
#     try:
#         PARAM = yaml.safe_load(stream)
#     except yaml.YAMLError as exc:
#         print(exc)

# umls_token = PARAM["umls_token"]
#https://uts-ws.nlm.nih.gov/rest/content/current/source/MSH/D014839/relations?apiKey=

#https://uts-ws.nlm.nih.gov/rest/content/current/source/HPO/HP:0002013/relations?includeRelationLabels=CHD&apiKey=
done = set()

def get_all_items(source_name: str, id: str, umls_token: str, includeRelationLabels: str="", additionalRelationLabel: str=""):
    extra_parameter = ""
    if includeRelationLabels != "":
        extra_parameter = f"includeRelationLabels={includeRelationLabels}"
    
    if additionalRelationLabel != "":
        extra_parameter += f"&includeAdditionalRelationLabels={additionalRelationLabel}"

    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/source/{source_name}/{id}/relations?{extra_parameter}&apiKey={umls_token}"
    #print (url)

    response = requests.get(url).json()

    if "status" in response and str(response["status"]) == "404":
        return []
    else:
        #print ("response", response)

        page_count = int(response["pageCount"])

        #print ("page_count", page_count)
        
        results = get_item(response, additionalRelationLabel)

        for i in range(2, page_count+1):
            new_url = url + f"&pageNumber={i}"

            new_response = requests.get(new_url).json()

            #print ("new_url", new_url)
            #print ("new_response", new_response)

            results += get_item(new_response)
        
        return results



def get_item(response: str, additionalRelationLabel: str=""):

    result = []
    
    if "result" not in response:
        return result

    else:
        for r in response["result"]:
            if r["classType"] == "AtomClusterRelation" and "relatedId" in r and "relatedIdName" in r:
                

                if additionalRelationLabel == "" or (additionalRelationLabel != "" and r["additionalRelationLabel"] == additionalRelationLabel):
                    item_parent_id = r["relatedId"].split("/")[-1]
                    item_name = r["relatedFromIdName"]
                    item_parent_name = r["relatedIdName"]

                    result.append((item_name, item_parent_id, item_parent_name))

        
        return result

def get_relation(subcategory_id: str, subcategory: str, umls_token: str, includeRelationLabels: str="", additionalRelationLabel: str=""):
    entities = []
    for entity in get_all_items(subcategory, subcategory_id, umls_token, includeRelationLabels, additionalRelationLabel):
        #print (entity)
        entities.append({"id": entity[1], "name": entity[2]})
    return entities

def recursive_get_subcategory_parent(subcategory_id: str, subcategory: str, umls_token: str, includeRelationLabels: str="", additionalRelationLabel: str=""):
    #print ("done", done)

    in_queue = queue.Queue()
    out_queue = queue.Queue()

    threads = 1

    def work():
        while True:
            son_subcategory_id = in_queue.get()
            #print ("son_subcategory_id", son_subcategory_id, get_all_items(subcategory, son_subcategory_id, "includeRelationLabels=CHD&includeAdditionalRelationLabels=isa", umls_token))

            #print (done)
            if son_subcategory_id not in done:
                #for entity in get_all_items("HPO", son_item_id, "includeRelationLabels=CHD&includeAdditionalRelationLabels=isa", umls_token):
                #print ("here", get_all_items(subcategory, son_subcategory_id, extra_parameter, umls_token))
                for entity in get_all_items(subcategory, son_subcategory_id, umls_token, includeRelationLabels, additionalRelationLabel):
                    out_queue.put((son_subcategory_id, entity[0], entity[1], entity[2]))
                    
                    in_queue.put(entity[1])
                done.add(son_subcategory_id)

            in_queue.task_done()
    
    for i in range(threads):
        
        t = Thread(target=work)
        t.daemon = True
        t.start()

    
    in_queue.put(subcategory_id)
        
    
    in_queue.join()   
 
    result = []
    
    while not out_queue.empty():
        
        result.append( out_queue.get())

    #print result
    
    return result

def search(query_name: str, umls_token: str, partial: bool=False, amount_of_results: int=3):

    url = f"https://uts-ws.nlm.nih.gov/rest/search/current?string={query_name}&apiKey={umls_token}&partialSearch={str(partial).lower()}"

    response = requests.get(url).json()

    #print ("response", response, type(response))

    if "status" in response and str(response["status"]) == "404":
        return []
    
    else:

        
        
        if "result" in response and "results" in response["result"]:
            result = []

            for r in response["result"]["results"]:
                if len(result) < amount_of_results and "ui" in r and "name" in r:
                    temp = {}
                    temp["cui"] = r["ui"]
                    temp["name"] = r["name"]
                    result.append(temp)
            return result
        else:    
            return []

def get_subcategory_id(umls: str, subcategory: str, umls_token: str):
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{umls}/atoms?&apiKey={umls_token}&sabs={subcategory}"

    response = requests.get(url).json()

    if "status" in response and str(response["status"]) == "404":
        return ""
    
    else:

        result = ""
        
        if "result" in response:

            for r in response["result"]:
                if "rootSource" in r and r["rootSource"] == subcategory and "code" in r:
                #if "rootSource" in r and r["rootSource"] == "MSH" and "code" in r:
                    
                    result = r["code"].split("/")[-1]

                    return result
        else:
                
            return result

def get_semantic_type(cui: str, umls_token: str):
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}?apiKey={umls_token}"

    response = requests.get(url).json()

    if "status" in response and str(response["status"]) == "404":
        return []
    
    else:

        
        
        if "result" in response:
            result = []
            
            if "semanticTypes" in response["result"]:
                for s in response["result"]["semanticTypes"]:
                    result.append(s["name"])

            return result
        else:
                
            return []

def get_name(MSH: str, umls_token: str):
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/source/MSH/{MSH}?apiKey={umls_token}"

    response = requests.get(url).json()

    #print ("response", response, type(response))

    if "status" in response and str(response["status"]) == "404":
        return ""
    
    else:

        result = ""
        if "result" in response and "name" in response["result"]:
            
            result = response["result"]["name"]
            
            return result
        else:
                
            return result



def get_substance_ATC_by_cui (cui: str, umls_token: str):
    atc_code = get_subcategory_id(cui, "ATC", umls_token)
    return atc_code

def get_substance_ATC_by_name (substrance: str, umls_token: str):
    cui = search(substrance, umls_token)
    atc_code = get_substance_ATC_by_cui(cui, umls_token)
    return atc_code

def get_cui_definition(cui: str, umls_token: str):
    url = f"https://uts-ws.nlm.nih.gov/rest/content/current/CUI/{cui}/definitions?apiKey={umls_token}"
    response = requests.get(url).json()


    if "status" in response and str(response["status"]) == "404":
        return ""
    
    else:
        result = ""
        if "result" in response:

            for r in response["result"]:
                if "rootSource" in r and r["rootSource"] == "MSH" and"value" in r:
            
                    result = r["value"]
            
                    return result
        else:
                
            return result


if __name__ == "__main__":
    #print(get_parent_HPO("HP:0000001", umls_token))
    #print(recursive_get_parent_HPO("HP:0011458", umls_token))

#### get may_be_prevented_by drugs of a disease
    #result = get_all_items("MSH", "D014839", "includeAdditionalRelationLabels=may_be_prevented_by", umls_token)

    #assert len(result) == 40
    #print (result)
    
#### recursive get all parent HPO
    #print ("\n\n")
    #print(recursive_get_parent_HPO("HP:0011458", umls_token))
###
    #print (get_all_items("MSH", "D015282", "includeAdditionalRelationLabels=isa", umls_token))
    #print (search("Gsk2256098", umls_token))
    #print (get_MSH("C2981865", umls_token))

    #print (get_name("C000604998", umls_token))
    #print (get_all_items("MSH", "C000604998", "includeAdditionalRelationLabels=mapped_to", umls_token))

    #name = get_subcategory_id("C0754187", "MSH", umls_token)

    #print (name)

    #print(get_substance_ATC_by_name("pralsetinib", umls_token))
    #print (search("ACYCLOVIR", umls_token))
    #print (get_semantic_type("C0001367", umls_token))

    print (get_cui_definition("C0019151", umls_token))