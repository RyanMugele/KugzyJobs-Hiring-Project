from app.nlp.job_parser import parse_job_description

test_cases = [
    {
        "name": "Test 1: Empty description",
        "description": "",
        "expected_error": ValueError
    },
    {
        "name": "Test 2: Unknown keywords",
        "description": "Looking for a creative person who works well with teams.",
        "expected": {
            "skills": [],
            "styles": [],
            "niches": []
        }
    },
    {
        "name": "Test 3: Duplicate skills",
        "description": "Must know CapCut, CapCut and Adobe Premiere Pro.",
        "expected": {
            "skills": ["capcut", "adobe premiere pro"],
            "styles": [],
            "niches": []
        }
    },
    {
        "name": "Test 4: Multiple categories",
        "description": (
            "Looking for a gaming editor skilled in Adobe Premiere Pro "
            "and After Effects for cinematic storytelling videos."
        ),
        "expected": {
            "skills": ["adobe premiere pro", "after effects"],
            "styles": ["cinematic", "storytelling"],
            "niches": ["gaming"]
        }
    },
    {
        "name": "Test 5: Documentary editor",
        "description": (
            "Looking for a documentary editor using DaVinci Resolve "
            "for color grading."
        ),
        "expected": {
            "skills": ["davinci resolve", "color grading"],
            "styles": [],
            "niches": ["documentary"]
        }
    }
]

passed = 0

for test in test_cases:
    print("\n" + "=" * 50)
    print(test["name"])

    try:
        result = parse_job_description(test["description"])
        if test.get("expected_error"):
           print("OVERALL: FAIL - Expected validation error was not raised")
           continue
        success = True

        for category in ["skills", "styles", "niches"]:
            actual = {v.casefold() for v in result[category]}
            expected = {v.casefold() for v in test["expected"][category]}

            matches = actual == expected
            success = success and matches

            print(f"{category.upper()}:")
            print(f"  Expected: {sorted(expected)}")
            print(f"  Actual:   {sorted(actual)}")
            print(f"  Result:   {'PASS' if matches else 'FAIL'}")

        if success:
            passed += 1
            print("OVERALL: PASS")
        else:
            print("OVERALL: FAIL")

    except Exception as error:
        expected_error = test.get("expected_error")

        if expected_error and isinstance(error, expected_error):
           passed += 1
           print(f"OVERALL: PASS - Correctly rejected empty description: {error}")
        else:
           print(f"OVERALL: ERROR - {error}")

print("\n" + "=" * 50)
print(f"FINAL RESULTS: {passed}/{len(test_cases)} tests passed")
