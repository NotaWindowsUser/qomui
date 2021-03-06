import json
import shlex
import logging
from subprocess import check_call, check_output, CalledProcessError
from collections import Counter

rootdir = "/usr/share/qomui"
saved_rules = []
saved_rules_6 = []
ip_cmd = ["iptables", "--wait",]
ip6_cmd = ["ip6tables", "--wait",]

def add_rule(rule):
    a = 1
    try:
        check = rule[:]
        if check[0] == "-A":
            check[0] = "-C"
        elif check[0] == "-I":
            check[0] = "-C"
            check.pop(2)
        elif check[2] == "-A":
            check[2] = "-C"
        apply_rule = check_call(ip_cmd + check)
        logging.debug("iptables: %s already exists" %rule)
        a = 0
    except (IndexError, CalledProcessError):
        pass
            
    try:
        if a == 1:
            apply_rule = check_call(ip_cmd + rule)
            logging.debug("iptables: applied %s" %rule)
        
    except CalledProcessError:
        logging.warning("iptables: failed to apply %s" %rule)
    
def add_rule_6(rule):
    try:
        apply_rule = check_call(ip6_cmd + rule)
        logging.debug("ip6tables: applied %s" %rule)
    except CalledProcessError:
        logging.warning("ip6tables: failed to apply %s" %rule)

def apply_rules(opt):
    firewall_rules = get_config()
    save_existing_rules(firewall_rules)
    save_existing_rules_6(firewall_rules)
        
    for rule in firewall_rules["flush"]:
        add_rule(rule)
        
    for rule in firewall_rules["flushv6"]:
        add_rule_6(rule)
        
    logging.info("iptables: flushed existing rules")

    for rule in saved_rules:
        add_rule(rule)
        
    for rule in saved_rules_6:
        add_rule_6(rule)
        
    if opt == 1:
        for rule in firewall_rules["defaults"]:
            add_rule(rule)
            
        for rule in firewall_rules["defaultsv6"]:
            add_rule_6(rule)
        
        for rule in firewall_rules["ipv4rules"]:
            add_rule(rule)

        for rule in firewall_rules["ipv6rules"]:
            add_rule_6(rule)
            
        logging.info("iptables: activated firewall")
        
    elif opt == 0:
        for rule in firewall_rules["unsecure"]:
            add_rule(rule)
            
        for rule in firewall_rules["unsecurev6"]:
            add_rule_6(rule)
            
        logging.info("iptables: deactivated firewall")
        
def save_existing_rules(firewall_rules):
    existing_rules = check_output(["iptables", "-S"]).decode("utf-8")
    for line in existing_rules.split('\n'):
        rpl = line.replace("/32", "")
        rule = shlex.split(rpl)
        if len(rule) != 0:
            match = 0
            omit = firewall_rules["ipv4rules"] + firewall_rules["flush"]
            for x in omit:
                if Counter(x) == Counter(rule):
                    match = 1
            if match == 0 and rule not in saved_rules:
                saved_rules.append(rule)
            match = 0
            
def save_existing_rules_6(firewall_rules):
    existing_rules = check_output(["ip6tables", "-S"]).decode("utf-8")
    for line in existing_rules.split('\n'):
        rpl = line.replace("/32", "")
        rule = shlex.split(rpl)
        if len(rule) != 0:
            match = 0
            omit = firewall_rules["ipv6rules"] + firewall_rules["flushv6"]
            for x in omit:
                if Counter(x) == Counter(rule):
                    match = 1
            if match == 0 and rule not in saved_rules_6:
                saved_rules_6.append(rule)
            match = 0

def allow_ping(opt):
    if opt == 1:
        firewall_rules = get_config()
        for rule in firewall_rules["allowping"]:
                add_rule(rule)
        logging.info("iptables: Ping allowed")
            
def get_config():
    try:
        with open ("%s/firewall.json" %(rootdir), "r") as f:
                return json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logging.debug("Loading default firewall configuration")
        try:
            with open ("%s/firewall_default.json" %(rootdir), "r") as f:
                    return json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
                logging.debug("Failed to load firewall configuration")
                return None
        
        

    

