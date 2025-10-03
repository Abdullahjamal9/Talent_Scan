# import fitz
# import json
# import requests
# import re
# import os

# def extract_text_from_pdf(pdf_path):
#     """
#     Extracts text from a PDF file using PyMuPDF (fitz).
#     """
#     try:
#         doc = fitz.open(pdf_path)
#         text = ""
#         for page in doc:
#             text += page.get_text("text") + "\n"
#         return text.strip()
#     except Exception as e:
#         print(f"Error extracting text from PDF {pdf_path}: {e}")
#         return None

# def parse_groq_response(response_text):
#     """
#     Parse the Groq AI response text into a structured dictionary.
#     """
#     try:
#         parsed_data = {
#             "name": "",
#             "email": "",
#             "gender": "",
#             "skills": [],
#             "experience": [],
#             "qualification": [],
#             "total_experience": 0
#         }

#         lines = response_text.split('\n')
#         current_field = None

#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue

#             if line.startswith('Name:'):
#                 parsed_data['name'] = line.replace('Name:', '').strip()
#             elif line.startswith('Email:'):
#                 parsed_data['email'] = line.replace('Email:', '').strip()
#             elif line.startswith('Gender:'):
#                 parsed_data['gender'] = line.replace('Gender:', '').strip()
#             elif line.startswith('Total Experience:'):
#                 # Extract numeric value from total experience
#                 experience_text = line.replace('Total Experience:', '').strip()
#                 try:
#                     # Try to extract the number from text like "5.5 years" or "5.5"
#                     number = float(re.search(r'(\d+(?:\.\d+)?)', experience_text).group(1))
#                     parsed_data['total_experience'] = number
#                 except:
#                     parsed_data['total_experience'] = 0
#             elif line.startswith('Skills:'):
#                 current_field = 'skills'
#                 skills_text = line.replace('Skills:', '').strip()
#                 if skills_text:
#                     skills = [skill.strip() for skill in skills_text.split(',')]
#                     skills = [skill for skill in skills if len(skill) > 1 and not skill.isdigit()]
#                     parsed_data['skills'] = sorted(list(set(skills)))
#             elif line.startswith('Experience:'):
#                 current_field = 'experience'
#                 continue
#             elif line.startswith('Qualification:'):
#                 current_field = 'qualification'
#                 qual_text = line.replace('Qualification:', '').strip()
#                 if qual_text:
#                     parsed_data['qualification'].append(qual_text)
#             elif current_field and (line.startswith('-') or (current_field == 'experience' and line)):
#                 item = line.replace('-', '').strip()
#                 if item:
#                     if current_field == 'skills':
#                         skills = [skill.strip() for skill in item.split(',')]
#                         parsed_data['skills'].extend(skills)
#                     elif current_field == 'experience':
#                         parsed_data['experience'].append(item)
#                     else:
#                         parsed_data[current_field].append(item)

#         # Clean and deduplicate skills list
#         if parsed_data['skills']:
#             parsed_data['skills'] = sorted(list(set([skill for skill in parsed_data['skills'] if len(skill) > 1])))

#         return parsed_data
#     except Exception as e:
#         print(f"Error parsing response: {e}")
#         return None

# def extract_resume_data(resume_text):
#     """
#     Send the resume text to Groq AI and extract required information.
#     """
#     API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
#     API_KEY = "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"

#     headers = {
#         "Authorization": f"Bearer {API_KEY}",
#         "Content-Type": "application/json"
#     }

#     # Extract potential email using regex
#     email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#     found_email = re.search(email_pattern, resume_text)
#     email_hint = f"\nPotential email found: {found_email.group(0)}" if found_email else ""

#     payload = {
#         "model": "mixtral-8x7b-32768",
#         "messages": [
#             {
#                 "role": "system",
#                 "content": (
#                     "You are an AI model specialized in parsing resumes. Extract information in this exact format:\n\n"
#                     "Name: [Extract full name from the top]\n"
#                     "Email: [Look for email in contact section]\n"
#                     "Gender: [Identify gender]\n"
#                     "Skills: [List ALL technical skills, programming languages, tools, frameworks, and soft skills as comma-separated list]\n"
#                     "Experience: [For each position, use format: 'Title: [Job Title] | Company: [Company Name] | StartDate: [MM/YYYY] | EndDate: [MM/YYYY or Present]' on separate lines]\n"
#                     "Total Experience: [Calculate total years of experience, format as decimal number]\n"
#                     "Qualification: [For each qualification, use format: 'Degree: [Degree Name] | Institution: [Institution Name] | StartDate: [MM/YYYY] | EndDate: [MM/YYYY]']\n\n"
#                     "IMPORTANT:\n"
#                     "1. Use the exact date format MM/YYYY (e.g., 03/2020)\n"
#                     "2. For current positions, use 'Present' as EndDate\n"
#                     "3. Extract all dates even if only year is mentioned (use 01/YYYY in such cases)\n"
#                     "4. If no month is mentioned for qualifications, default to graduation month as 05/YYYY\n"
#                     "5. Keep all sections separated with ' | ' delimiter\n"
#                     "6. Include every position and qualification\n"
#                     "7. List most recent items first"
#                 )
#             },
#             {
#                 "role": "user",
#                 "content": (
#                     "Parse this resume completely, including ALL dates in the experience section. "
#                     f"Resume text:{email_hint}\n\n{resume_text}"
#                 )
#             }
#         ],
#         "temperature": 0.2,
#         "max_tokens": 2000
#     }

#     try:
#         response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
#         response.raise_for_status()

#         if response.status_code == 200:
#             response_content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
#             if not response_content:
#                 raise ValueError("Empty response from API")

#             parsed_data = parse_groq_response(response_content)
#             if not parsed_data:
#                 raise ValueError("Failed to parse API response")

#             # Use regex-found email if AI didn't find one
#             if (not parsed_data['email'] or parsed_data['email'] == 'Not found') and found_email:
#                 parsed_data['email'] = found_email.group(0)

#             return parsed_data

#     except requests.exceptions.Timeout:
#         print("Request timed out")
#     except requests.exceptions.RequestException as e:
#         print(f"API request failed: {e}")
#     except Exception as e:
#         print(f"Error processing resume: {e}")

#     return None

# def process_resumes(resume_paths):
#     """
#     Process multiple resumes and return results as a JSON-compatible dictionary.
#     """
#     results = []

#     for resume_path in resume_paths:

#         adjusted_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../", resume_path.lstrip("/")))

#         resume_result = {
#             "file_path": adjusted_path,
#             "status": "failed",
#             "data": None,
#             "error": None
#         }

#         try:
#             resume_text = extract_text_from_pdf(adjusted_path)

#             if resume_text:
#                 extracted_data = extract_resume_data(resume_text)
#                 if extracted_data:
#                     if extracted_data.get('name') and extracted_data.get('email'):
#                         resume_result["status"] = "success"
#                         resume_result["data"] = extracted_data
#                     else:
#                         resume_result["error"] = "Missing required fields (name or email)"
#                 else:
#                     resume_result["error"] = "Failed to extract or parse data"
#             else:
#                 resume_result["error"] = "Failed to extract text from PDF"

#         except Exception as e:
#             resume_result["error"] = f"Error processing resume: {str(e)}"

#         results.append(resume_result)

#     return results

import fitz
import json
import requests
import re
import os
from typing import List, Dict, Any

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return None

def parse_groq_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the Groq AI response text into a structured dictionary.
    """
    try:
        parsed_data = {
            "name": "",
            "email": "",
            "gender": "",
            "age": 0,
            "bio": [],
            "skills": [],
            "experience": [],
            "qualification": [],
            "total_experience": 0
        }

        lines = response_text.split('\n')
        current_field = None
        experience_entries = []
        qualification_entries = []
        bio_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('Name:'):
                parsed_data['name'] = line.replace('Name:', '').strip()
            elif line.startswith('Email:'):
                parsed_data['email'] = line.replace('Email:', '').strip()
            elif line.startswith('Gender:'):
                parsed_data['gender'] = line.replace('Gender:', '').strip()
            elif line.startswith('Total Experience:'):
                experience_text = line.replace('Total Experience:', '').strip()
                try:
                    number = float(re.search(r'(\d+(?:\.\d+)?)', experience_text).group(1))
                    parsed_data['total_experience'] = number
                except:
                    parsed_data['total_experience'] = 0
            elif line.startswith('Age:'):
                age_text = line.replace('Age:', '').strip()
                try:
                    parsed_data['age'] = int(re.search(r'(\d+)', age_text).group(1))
                except:
                    parsed_data['age'] = 0
            elif line.startswith('Bio:'):
                current_field = 'bio'
                bio_text = line.replace('Bio:', '').strip()
                if bio_text:
                    bio_lines.append(bio_text)
            elif line.startswith('Skills:'):
                current_field = 'skills'
                skills_text = line.replace('Skills:', '').strip()
                if skills_text:
                    skills = [skill.strip() for skill in skills_text.split(',')]
                    skills = [skill for skill in skills if len(skill) > 1 and not skill.isdigit()]
                    parsed_data['skills'] = sorted(list(set(skills)))
            elif line.startswith('Experience:'):
                current_field = 'experience'
                continue
            elif line.startswith('Qualification:'):
                current_field = 'qualification'
                continue
            elif current_field == 'bio' and not line.startswith('Skills:') and not line.startswith('Experience:'):
                bio_lines.append(line)
            elif current_field == 'experience' and line:
                experience_entries.append(line.replace('-', '').strip())
            elif current_field == 'qualification' and line:
                qualification_entries.append(line.replace('-', '').strip())

        parsed_data['bio'] = ' '.join(bio_lines).strip()
        parsed_data['experience'] = experience_entries
        parsed_data['qualification'] = qualification_entries

        if parsed_data['skills']:
            parsed_data['skills'] = sorted(list(set([skill for skill in parsed_data['skills'] if len(skill) > 1])))

        return parsed_data
    except Exception as e:
        return None

def extract_resume_data(resume_text: str) -> Dict[str, Any]:
    """
    Send the resume text to Groq AI and extract required information.
    """
    API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    API_KEY = "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"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    found_email = re.search(email_pattern, resume_text)
    email_hint = f"\nPotential email found: {found_email.group(0)}" if found_email else ""

    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI model specialized in parsing resumes. Extract information in this exact format:\n\n"
                    "Name: [Extract full name from the top]\n"
                    "Email: [Look for email in contact section]\n"
                    "Gender: [Identify gender]\n"
                    "Age: [Identify or estimate age]\n"
                    "Bio: [Extract or summarize personal profile/summary/objective statement in 2-3 sentences]\n"
                    "Skills: [List ALL technical skills, programming languages, tools, frameworks, and soft skills as comma-separated list]\n"
                    "Experience: [For each position, use format: 'Title: [Job Title] | Company: [Company Name] | StartDate: [MM/YYYY] | EndDate: [MM/YYYY or Present]' on separate lines]\n"
                    "Total Experience: [Calculate total years of experience, format as decimal number]\n"
                    "Qualification: [For each qualification, use format: 'Degree: [Degree Name] | Institution: [Institution Name] | StartDate: [MM/YYYY] | EndDate: [MM/YYYY]']\n\n"
                    "IMPORTANT:\n"
                    "1. Use the exact date format MM/YYYY (e.g., 03/2020)\n"
                    "2. For current positions, use 'Present' as EndDate\n"
                    "3. Extract all dates even if only year is mentioned (use 01/YYYY in such cases)\n"
                    "4. If no month is mentioned for qualifications, default to graduation month as 05/YYYY\n"
                    "5. Keep all sections separated with ' | ' delimiter\n"
                    "6. Include every position and qualification\n"
                    "7. List most recent items first"
                    "8. If age is not explicitly stated, make a reasonable estimate based on graduation dates and experience\n"
                    "9. For Bio, extract any personal statement, summary, or objective and summarize in 2-3 sentences"
                )
            },
            {
                "role": "user",
                "content": f"Parse this resume completely, ensuring all dates are in MM/YYYY format:{email_hint}\n\n{resume_text}"
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        if response.status_code == 200:
            response_content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if not response_content:
                return None

            parsed_data = parse_groq_response(response_content)
            if not parsed_data:
                return None

            # Parse experience entries into structured format
            structured_experience = []
            for exp in parsed_data['experience']:
                parts = exp.split(' | ')
                exp_entry = {}
                for part in parts:
                    if part.startswith('Title:'):
                        exp_entry['title'] = part.replace('Title:', '').strip()
                    elif part.startswith('Company:'):
                        exp_entry['company'] = part.replace('Company:', '').strip()
                    elif part.startswith('StartDate:'):
                        exp_entry['start_date'] = part.replace('StartDate:', '').strip()
                    elif part.startswith('EndDate:'):
                        exp_entry['end_date'] = part.replace('EndDate:', '').strip()
                if exp_entry:
                    structured_experience.append(exp_entry)
            
            # Parse qualification entries into structured format
            structured_qualification = []
            for qual in parsed_data['qualification']:
                parts = qual.split(' | ')
                qual_entry = {}
                for part in parts:
                    if part.startswith('Degree:'):
                        qual_entry['degree'] = part.replace('Degree:', '').strip()
                    elif part.startswith('Institution:'):
                        qual_entry['institution'] = part.replace('Institution:', '').strip()
                    elif part.startswith('StartDate:'):
                        qual_entry['start_date'] = part.replace('StartDate:', '').strip()
                    elif part.startswith('EndDate:'):
                        qual_entry['end_date'] = part.replace('EndDate:', '').strip()
                if qual_entry:
                    structured_qualification.append(qual_entry)
            
            parsed_data['experience'] = structured_experience
            parsed_data['qualification'] = structured_qualification

            if (not parsed_data['email'] or parsed_data['email'] == 'Not found') and found_email:
                parsed_data['email'] = found_email.group(0)

            return parsed_data

    except Exception as e:
        print(e, "qqqqqqqqqqqqqqqqqqqq")
        return None

def process_resumes(resume_paths: List[str]) -> Dict[str, Any]:
    """
    Process multiple resumes and return results as a JSON-compatible dictionary.
    """
    output = {
        "timestamp": "",
        "total_resumes": len(resume_paths),
        "successful_processes": 0,
        "failed_processes": 0,
        "results": []
    }

    for resume_path in resume_paths:
        adjusted_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../", resume_path.lstrip("/")))
        # print(adjusted_path)
        resume_result = {
            "file_path": adjusted_path,
            "status": "failed",
            "processing_time": "",
            "data": None,
            "error": None
        }

        try:
            resume_text = extract_text_from_pdf(adjusted_path)
            # print(resume_text)
            if resume_text:
                extracted_data = extract_resume_data(resume_text)
                # print(extracted_data)
                if extracted_data:
                    if extracted_data.get('name') and extracted_data.get('email'):
                        resume_result["status"] = "success"
                        resume_result["data"] = extracted_data
                        output["successful_processes"] += 1
                    else:
                        resume_result["error"] = "Missing required fields (name or email)"
                        output["failed_processes"] += 1
                else:
                    resume_result["error"] = "Failed to extract or parse data"
                    output["failed_processes"] += 1
            else:
                resume_result["error"] = "Failed to extract text from PDF"
                output["failed_processes"] += 1

        except Exception as e:
            print("eeeeeeeeeeeeeeeeeeeeee")
            resume_result["error"] = str(e)
            output["failed_processes"] += 1

        output["results"].append(resume_result)

    return output
