from utils.rule_parser import RuleSet
import argparse

def main():
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("rules", help="Path of the file containing the rules")
    parser.add_argument("module", help="Path of the file containing the WASM module to analyze")
    # parser.add_argument("--greeting", "-g", default="Hello", help="Custom greeting message")

    args = parser.parse_args()
    rule_set = RuleSet(args.rules)
    print(rule_set)
    # TODO: call wassail with given input
    
    # TODO: with the wassail output + rule set, call manticore

if __name__ == "__main__":
    main()