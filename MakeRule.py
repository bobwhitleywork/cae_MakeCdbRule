import os
import sys
import Utils.CDB
import xml.etree.ElementTree as ET
import shutil

BACKUP_DIRECTORY = r"d:\backup\MakeRule"
CONFIG_FILE_DIRECTORY = r"D:\cae-fg3d\Trunk\CDB_Validator_Version_2\ConfigFiles"
README_FILENAMES = ['ReadMeTemplate.txt', 'ReadMe.txt']
RULE_FILENAMES = ['NewRuleTemplate.py', 'Rule.py']
TEMPLATE_DIRECTORY = r"D:\cae-fg3d\Trunk\CDB_Validator_Version_2\Documentation"
TEST_CDB_DIRECTORY_NAME_TEMPLATE = '{pass_fail}RuleCDB_{rule_number}'
VALIDATOR_DIRECTORY = r"D:\cae-fg3d\Trunk\CDB_Validator_Version_2"

CONFIG_FILE_TEMPLATE = '''
<?xml version="1.0" encoding="utf-8"?>
<Configuration>

<CDB_Root>
  <!--<Folder path = "${work_dir}/Integrity/{rule_name}/{pass_fail}RuleCDB_{rule_number}" />-->
  <Folder path="D:\CDB\CDB_R1_OYAA_DEV_R11_20101128_72" />
</CDB_Root>
  
<Database>
  <Hostname value = "localhost"/>
  <Username value = "postgres"/>
  <Port value = "5432"/>
</Database>

<CDB_Check>
  <Name>{rule_name}</Name>
</CDB_Check>

</Configuration>
'''

RuleNumber = None
RuleDirectory = None
RuleName = None


def AddAllRulesConfigItem(previousRuleName):

	# create new element
	cdbCheck = ET.Element("CDB_Check")
	cdbCheck.text = '\n  '
	cdbCheck.tail = '\n\n'
	name = ET.SubElement(cdbCheck, "Name")
	name.text = RuleName
	name.tail = '\n'

	# open AllRulesConfig.xml
	allRulePath = os.path.join(VALIDATOR_DIRECTORY, 'AllRulesConfig.xml')
	CopyToBackupDir(allRulePath)
	tree = ET.parse(allRulePath)
	root = tree.getroot()

	# find insert location
	insertIndex = -1
	for i in range(len(root)):
		
		element = root[i]
		if element.tag != 'CDB_Check':
			continue
		
		nameElement = element.find('Name')
		if not nameElement is None and nameElement.text.strip().lower() == previousRuleName.lower():
			insertIndex = i
			break

	if insertIndex == -1:
		print(f'Couldn\'t find {previousRuleName} in AllRulesConfigTest.xml')
		return

	# insert element
	root.insert(insertIndex + 1, cdbCheck)

	# save file
	try:
		tree.write(allRulePath)
		print(f'Modified {allRulePath}')
	except Exception as ex:
		print(f'Failed to modify {allRulePath}. {ex}')




class AddManifestItemClass:
	def __init__(self, manifestIndex, previousRuleName):
		self.itemIndex = manifestIndex
		self.previousRuleName = previousRuleName

def AddManifestItem():
	def GetFirstRuleNumber(allNumbers:str):
		return allNumbers.lstrip().split(' ')[0]


	# create new element
	cdbCheck = ET.Element("CDB_Check")
	cdbCheck.text = '\n  '
	cdbCheck.tail = '\n\n'
	name = ET.SubElement(cdbCheck, "Name")
	name.text = RuleName
	name.tail = '\n  '
	folder = ET.SubElement(cdbCheck, "Folder", path=RuleDirectory.replace('\\', '/'))
	folder.tail = '\n  '
	rule = ET.SubElement(cdbCheck, "Rule")
	rule.text = f' {RuleNumber} '
	rule.tail = '\n'

	# open manifest.xml
	manifestPath = os.path.join(VALIDATOR_DIRECTORY, 'RulesManifest.xml')
	CopyToBackupDir(manifestPath)
	tree = ET.parse(manifestPath)
	root = tree.getroot()

	# find insert location
	insertIndex = 0
	thisRuleNumber = 0
	for rule in root.iter('Rule'):
		insertIndex += 1
		firstRuleNumber = GetFirstRuleNumber(rule.text)

		if Utils.CDB.RepresentsInt(firstRuleNumber):
			thisRuleNumber = int(firstRuleNumber)
		else:
			print(f'Bad rule number: {rule.text}')
			continue

		if int(RuleNumber) < thisRuleNumber:
			insertIndex -= 1
			break

	prevRuleName = ''
	if insertIndex > 0:
		prevRuleName = root[insertIndex - 1][0].text
	
	

	# insert element
	root.insert(insertIndex, cdbCheck)

	# save file
	tree.write(r"D:\cae-fg3d\Trunk\CDB_Validator_Version_2\RuleManifestTest.xml")

	return AddManifestItemClass(insertIndex, prevRuleName)

	# file = open(r"D:\cae-fg3d\Trunk\CDB_Validator_Version_2\RuleManifestTest.xml", 'w')
	# file.write(ET.tostring(xmlRoot))
	# file.close()

def CopyToBackupDir(filePath):

	if not os.path.isfile(filePath):
		return (False, f'Unable to find file {filePath}')

	if not os.path.isdir(BACKUP_DIRECTORY):
		os.mkdir(BACKUP_DIRECTORY)

	filename = os.path.basename(filePath)
	stem = os.path.splitext(filename)[0]
	extension = os.path.splitext(filename)[1]
	counter = 0

	while 1:
		backupFilename = os.path.join(BACKUP_DIRECTORY, f'{stem}_{str(counter).zfill(5)}{extension}')
		if os.path.isfile(backupFilename):
			counter += 1
			continue

		try:
			shutil.copyfile(filePath, backupFilename)
		except Exception as ex:
			msg = f'Failed to backup {filePath}. {ex}'
			print(msg)
			return (False, msg)

		msg = f'Backed up {filePath}'
		print(msg)
		return (True, msg)

def CreateConfigFiles():

	for passFail in ['Pass', 'Fail']:

		isSuccessful = True
		messages = []
		
		filename = os.path.join(CONFIG_FILE_DIRECTORY, f'Rule_{RuleNumber}_{passFail}.xml')
		if os.path.isfile(filename):
			print(f'{filename} exists. Did not create new file.')
			continue

		try:
			f = open(filename, 'w')
			f.write(CONFIG_FILE_TEMPLATE.format(rule_name=RuleName, pass_fail=passFail, rule_number=RuleNumber, work_dir='{work_dir}'))
			print(f'Created {filename}')
		except Exception as ex:
			msg = f'Error creating {filename}. {ex}'
			print(msg)
			isSuccessful = False
			messages.append(msg)
		finally:
			f.close

	return (isSuccessful, messages)

def CreatePopulateRuleDir():
	
	returnMessages = []
	isSuccessful = True

	# quit if directory exists
	ruleDirectory = os.path.join(VALIDATOR_DIRECTORY, RuleDirectory)
	if os.path.isdir(ruleDirectory):
		msg = f'Directory {ruleDirectory} exists'
		print(msg)
		return (False, [msg])

	# make the rule directory
	try:
		os.mkdir(ruleDirectory)
	except Exception as ex:
		msg = f'Create directory {ruleDirectory} failed. {ex}'
		print(msg)
		return (False, [msg])

	# make test CDB directories
	for passFail in ['Pass', 'Fail']:
		dirPath = os.path.join(ruleDirectory, TEST_CDB_DIRECTORY_NAME_TEMPLATE.format(pass_fail=passFail, rule_number=RuleNumber))
		try:
			os.mkdir(dirPath)
			f = open(os.path.join(dirPath, '.placeholder'), 'w')
			f.write('placeholder')
			f.close()
		except Exception as ex:
			msg = f'Failed to create directory {dirPath}'
			print(msg)
			returnMessages.append(msg)

	# copy the template files to the new dir
	for source, target in [README_FILENAMES, RULE_FILENAMES]:
		newFilepath = os.path.join(ruleDirectory, target)
		try:
			shutil.copyfile(os.path.join(TEMPLATE_DIRECTORY, source), newFilepath)
		except Exception as ex:
			msg = f'Unable to copy template to {newFilepath}. {ex}'
			print (msg)
			returnMessages.append(msg)
			isSuccessful = False

		if os.path.isfile(newFilepath):
			print (f'Copied template to rule directory ({newFilepath})')

def ModifyRuleFile():
	
	isSuccessful = True
	messages = []
	rulePathname = os.path.join(VALIDATOR_DIRECTORY, RuleDirectory, 'Rule.py')

	if not os.path.isfile(rulePathname):
		msg = f'Unable to find {rulePathname}'
		print(msg)
		return (False, [msg])

	f = None
	try:
		f = open(rulePathname, 'r')
	except Exception as ex:
		msg = f'Failed to open file {rulePathname}. {ex}'
		print (msg)
		return (False, [msg])

	newContent = []
	line = f.readline()
	while line:

		line = line.replace('YourNewRule', RuleName)

		if line.strip() == '# ToDo:': # skip this line and the next one
			line = f.readline()

		elif line.strip() == 'def Run(self):': # skip all lines until 'return'
			newContent.append(line + '\n\n\n')
			while line.strip() != 'return':
				line = f.readline()
			newContent.append(line)

		else:
			newContent.append(line)

		line = f.readline()

	f.close()

	# write new file
	try:
		os.remove(rulePathname)
		f = open(rulePathname, 'w')
		
		for line in newContent:
			f.write(f'{line}')

	except Exception as ex:
		msg = f'Unable to write output file {rulePathname}. {ex}'
		print (msg)
		return (False, [msg])
	finally:
		f.close()

	if os.path.isfile(rulePathname):
		print(f'Modified {rulePathname}')




def Main():

	# add item to RuleManifest.xml
	manifestInfo = AddManifestItem()

	# add item to AllRulesConfig.xml
	AddAllRulesConfigItem(manifestInfo.previousRuleName)

	# create the pass/fail config files
	CreateConfigFiles()

	# create rule dir and insert initial files and dirs
	CreatePopulateRuleDir()

	# make changes to the rule.py file
	ModifyRuleFile()

def BadParameters(tattleTale):
	print(f'USAGE: py MakeRule.py <ruleNumber> <directory> ({tattleTale})')
	exit(1)

if __name__ == '__main__':


	if len(sys.argv) < 2:
		BadParameters('001')

	if not Utils.CDB.RepresentsInt(sys.argv[1]):
		BadParameters('002')

	RuleNumber = sys.argv[1]
	RuleDirectory = sys.argv[2]
	
	parts = RuleDirectory.replace('\\', '/').split('/') # take care of both kinds of delimiters
	RuleName = parts[len(parts)-1]

	Main()

	
