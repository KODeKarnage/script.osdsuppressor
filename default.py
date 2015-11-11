#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (C) 2015 KodeKarnage
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

import os
import re
import subprocess
import xml.etree.ElementTree as ET


__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')
__setting__      = __addon__.getSetting


def Main():

	delay = int(__setting__('delay'))

	xbmc.log('OSD Suppressor delay == %s' % delay)

	skin = xbmc.translatePath('special://skin')

	brake = False

	create_backup = False

	pause_found = False

	for dirpath, dnames, fnames in os.walk(skin):
		if brake:
			break
		for f in fnames:
			if f == 'DialogSeekBar.xml':
				osd_file = f
				osd_path = dirpath
				osd_fullpath = os.path.join(dirpath, f)
				
				brake = True
				break
	else: # no break

		xbmc.log('OSD Suppressor: file not found')
	
		return

	tree = ET.parse(osd_fullpath)
	window = tree.getroot()
	visibles = window.findall('visible')
	includes = window.findall('includes')

	# see if you can follow INCLUDES tags to their appropriate VISIBLE tags
	# basically, we have to find Player.Paused and change all instances

	for visible in visibles:
		current_text = visible.text

		current_text = current_text.replace(' ','')

		if 'Player.Paused' in current_text and 'IdleTime(%s)' % delay not in current_text:

			xbmc.log('OSD Suppressor: xml file valid for change.')

			pause_found = True

			# while this regex should only match where we have alreay made an adjustment to the skin file
			regex = re.compile(r".*(\[Player.Paused\+!System\.IdleTime\(\d*\)\]).*", re.IGNORECASE)
			regex_bracketed = re.compile(r"(Player.Paused\+!System\.IdleTime\(\d*\))", re.IGNORECASE)
			
			# this regex should match an existing skin entry
			regex_original = re.compile(r"(!System\.IdleTime\(\d*\)\+)?Player.Paused(\+!System\.IdleTime\(\d*\))?", re.IGNORECASE)
			
			if re.match(regex, current_text):

				xbmc.log('OSD Suppressor: bracketed regex found')

				new_text = regex_bracketed.sub('Player.Paused+!System.IdleTime(%s)' % delay, current_text)

			else:

				xbmc.log('OSD Suppressor: normal regex found')

				new_text = regex_original.sub('[Player.Paused+!System.IdleTime(%s)]' % delay, current_text)

				create_backup = True
		
			new_visible = ET.Element('visible')
			new_visible.text = new_text
			window.remove(visible)
			window.insert(0, new_visible)
			xbmc.log('OSD Suppressor: New Condition: %s' % new_text)

		elif 'IdleTime' in current_text:

			xbmc.log('OSD Suppressor: IdleTime(%s) already in DialogSeekBar.xml' % delay)

			pause_found = True

			continue

	temp_location = os.path.join(xbmc.translatePath('special://userdata/'),'addon_data',__addonid__)

	temp_file = os.path.join(temp_location, osd_file)

	if not os.path.isdir(temp_location):
		try:
			os.mkdir(temp_location)
			xbmc.log('OSD Suppressor: temp file location doesnt exist, folder created.')
		except:
			self.log('OSD Suppressor: temp file location doesnt exist, failed to create folder.')
			return

	tree.write(temp_file, xml_declaration=True)

	xbmc.log('OSD Suppressor: temp file created: %s' % temp_file)

	if create_backup:

		# only backup the original file

		result1 = xbmcvfs.copy(osd_fullpath, os.path.join(osd_path, osd_file.replace('Bar.xml','BarBackup.xml')))

		xbmc.log('OSD Suppressor: Result of copy1 - %s' % result1)
		
		if not result1:

			xbmc.log('OSD Suppressor: Trying alternative copy method1')

			subprocess.call(['sudo', 'cp', osd_fullpath, osd_fullpath.replace('Bar.xml', 'BarBackup.xml')])
			subprocess.call(['cp', osd_fullpath, osd_fullpath.replace('Bar.xml', 'BarBackup.xml')])

	result2 = xbmcvfs.copy(temp_file, osd_path)

	xbmc.log('OSD Suppressor: Result of copy2 - %s' % result2)

	if not result2:

		xbmc.log('OSD Suppressor: Trying alternative copy method2')

		subprocess.call(['sudo', 'cp', temp_file, osd_fullpath])
		subprocess.call(['cp', temp_file, osd_fullpath])

if __name__ == "__main__":
	Main()