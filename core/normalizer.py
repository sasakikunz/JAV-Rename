import re
import os

from core.cache_manager import CacheManager


class MovieNormalizer:
    def __init__(self, cache_file='prefix_cache.json', example_pairs=None):
        self.suffix_tags = ['-C', 'ch', '_UNC', '_C', 'C', 'uncensored', 'Leaked', 'U']
        self.cache_manager = CacheManager(cache_file)
        self.known_prefixes = self.cache_manager.load()

        if example_pairs:
            self.learn_prefixes(example_pairs)
            self.cache_manager.save(self.known_prefixes)

    def learn_prefixes(self, pairs):
        for original, normalized in pairs:
            if not normalized or normalized.strip() == '' or normalized.strip() == 'nan':
                normalized = original

            normalized = re.sub(r'\[|\]', '', normalized)

            parts = normalized.split()
            if parts:
                normalized = parts[0]

            fc2_match = re.search(r'(FC2-PPV-\d+|fc2ppv-\d+)', normalized)
            if fc2_match:
                continue

            match = re.match(r'([A-Za-z0-9]+?)-(\d+)', normalized)
            if match:
                prefix = match.group(1).upper()
            else:
                match = re.match(r'([A-Za-z]+)(\d+)', normalized)
                if match:
                    prefix = match.group(1).upper()
                else:
                    continue
            self.known_prefixes.add(prefix)

    def _process_fc2(self, original):
        fc2_patterns = [
            r'FC2-PPV-(\d+)',
            r'FC2PPV-?(\d+)',
            r'fc2ppv[_-]?(\d+)',
            r'FC2 PPV (\d+)',
            r'fc(\d{7})',
        ]

        for pattern in fc2_patterns:
            match = re.search(pattern, original, re.IGNORECASE)
            if match:
                num = match.group(1)
                if pattern.startswith(r'fc(\d'):
                    return f"FC2-PPV-{num}", True
                return f"FC2-PPV-{num}", True
        return None, False

    def _process_carib(self, original):
        carib_6digit = r'[Cc]arib[a-z]*[_-]?(\d{6})[_-](\d{3})'
        caribpr_pattern = r'Caribpr\s+(\d{6})[_-](\d{3})'
        caribbean_pattern = r'[Cc]aribbean[_-]?\s+(\d{6})[_-](\d{3})'
        carib_8digit = r'[Cc]arib[a-z]*[_-]?(\d{8})'
        caribcom_pattern = r'[Cc]aribbeancom\s*[–-]?\s*(\d{6})[_-](\d{3})'

        match = re.search(carib_6digit, original)
        if match:
            return f"{match.group(1)}-{match.group(2)}", True

        match = re.search(caribpr_pattern, original)
        if match:
            return f"{match.group(1)}-{match.group(2)}", True

        match = re.search(caribbean_pattern, original)
        if match:
            return f"{match.group(1)}-{match.group(2)}", True

        match = re.search(caribcom_pattern, original)
        if match:
            return f"{match.group(1)}-{match.group(2)}", True

        match = re.search(carib_8digit, original)
        if match:
            return f"CARIB-{match.group(1)}", True

        return None, False

    def _process_divx_nike(self, original):
        match = re.search(r'DivX\+nike\(([A-Za-z]+)(\d+)\)', original, re.IGNORECASE)
        if match:
            prefix, num = match.groups()
            return f"{prefix.upper()}-{num}", True
        return None, False

    def _process_cwp(self, original):
        match = re.match(r'(CWP[DB]?)[._](\d+)', original, re.IGNORECASE)
        if match:
            prefix = match.group(1).upper()
            num = match.group(2)
            return f"{prefix}-{num}", True
        return None, False

    def _process_heyzo(self, original):
        match = re.search(r'[Hh][Ee][Yy][Zz][Oo]\s+(\d{3,4})', original)
        if match:
            num = match.group(1)
            return f"HYEZO-{num}", True
        return None, False

    def _clean_non_ascii(self, s):
        return re.sub(r'[^\x00-\x7F]+', '', s)

    def _remove_video_extensions(self, s):
        s = re.sub(r'\.(mp4|mkv|avi|wmv|mov|flv|ts|m2ts|webm|zip|m4v)$', '', s, flags=re.IGNORECASE)
        s = re.sub(r'(MP4|AVI|MKV|MOV|FLV)$', '', s, flags=re.IGNORECASE)
        s = re.sub(r'[-_]?(mp4|mkv|avi|wmv|mov|flv|m4v)$', '', s, flags=re.IGNORECASE)
        return s

    def _remove_resolution_tags(self, s):
        s = re.sub(r'[-_]?(FHD|(?<![A-Z])HD\b|1080p|720p|4K|8K|2K|UHD|30p|60p|Leaked)', '', s, flags=re.IGNORECASE)
        s = re.sub(r'[-_](GG5|X1080X|RUNBKK)', '', s, flags=re.IGNORECASE)
        s = re.sub(r'\.(HD|FHD|1080p|720p)\b', '', s, flags=re.IGNORECASE)
        s = re.sub(r'UNCENSORED', '', s, flags=re.IGNORECASE)
        s = re.sub(r'[-_]?UNC\b', '', s, flags=re.IGNORECASE)
        s = re.sub(r'[-_]?(uncensored)\b', '', s, flags=re.IGNORECASE)
        return s

    def _remove_xyz_domain(self, s):
        s = re.sub(r'[a-zA-Z0-9-]+\.(?:com|tv|me|la|xyz|cc|net|org|pro)[@-]?', '', s, flags=re.IGNORECASE)
        s = s.replace('@', ' ')
        return s

    def _remove_date_patterns(self, s):
        s = re.sub(r'\d{4}-\d{2}-\d{2}', '', s)
        s = re.sub(r'\d{4}_\d{2}_\d{2}', '', s)
        s = re.sub(r'\[\d{4}-\d{2}-\d{2}\]', '', s)
        return s

    def _remove_site_names(self, s):
        s = re.sub(r'S-CUTE', '', s, flags=re.IGNORECASE)
        s = re.sub(r'S-Cute', '', s, flags=re.IGNORECASE)
        s = re.sub(r's-cute', '', s, flags=re.IGNORECASE)
        return s

    def _preprocess_disc_suffixes(self, s):
        s = re.sub(r'_(\d)(?:\.[a-zA-Z0-9]+)?$', r'_CD\1', s)
        s = re.sub(r'-(\d)$', r'-CD\1', s)
        s = re.sub(r'\s*\(\d+\)', '', s)
        s = re.sub(r'\s+\d+$', '', s)
        return s

    def _remove_ad_text(self, s):
        s = re.sub(r'第一會所新片@\w+@', '', s)
        s = re.sub(r'mm\d+@[^@]*@', '', s)
        s = re.sub(r'第一会所@', '', s)
        s = re.sub(r'\w+@18p2p@', '', s)
        s = re.sub(r'@18p2p', '', s)
        s = re.sub(r'1pondo', '', s, flags=re.IGNORECASE)
        s = re.sub(r'Caribbean', '', s, flags=re.IGNORECASE)
        s = re.sub(r'Caribpr', '', s, flags=re.IGNORECASE)
        s = re.sub(r'_Vol\s*\d*$', '', s)
        return s

    def _extract_code_with_prefix_check(self, s, orig_upper):
        upper_s = s.upper()
        
        for p in sorted(self.known_prefixes, key=lambda x: -len(x)):
            p_upper = p.upper()
            
            # 在整个字符串中查找前缀
            pattern = re.compile(re.escape(p_upper) + r'[_-]?([A-Z]?\d+)', re.IGNORECASE)
            match = pattern.search(s)
            
            if match:
                num_raw = match.group(1)
                if num_raw.isdigit() and len(num_raw) >= 5:
                    num = str(int(num_raw))
                else:
                    num = num_raw
                
                # 检查后面是否有后缀
                suffix = s[match.end():]
                
                # 先检查CD后缀（如-CD1、-CD2）
                cd_suffix = ''
                cd_match = re.match(r'-CD(\d+)$', suffix, re.IGNORECASE)
                if cd_match:
                    cd_suffix = f'-CD{cd_match.group(1)}'
                    suffix = suffix[:-len(cd_suffix)]
                
                # 检查-C后缀（ch/C）和分集后缀（A/B）
                has_c = False
                c_match = re.match(r'[-_]?(ch|C)$', suffix, flags=re.IGNORECASE)
                ab_match = re.match(r'[-_]?(A|B)$', suffix, flags=re.IGNORECASE)
                if c_match:
                    has_c = True
                elif ab_match:
                    letter = ab_match.group(1).upper()
                    cd_suffix = f'-CD{1 if letter == "A" else 2}'
                
                final_code = f"{p_upper}-{num}"
                if has_c and not final_code.endswith('-C'):
                    final_code += '-C'
                final_code += cd_suffix
                
                return final_code, True
        
        return None, False

    def _general_extract(self, s):
        s_upper = s.upper()

        match = re.match(r'^(\d{6})-(\d{3})(-CD\d+)?$', s_upper)
        if match:
            num1 = match.group(1)
            num2 = match.group(2)
            cd = match.group(3) or ''
            return f"{num1}-{num2}{cd}", True

        match = re.match(r'^([A-Z]+)-(\d+)(.*)', s_upper)
        if match:
            prefix = match.group(1)
            num = match.group(2)
            rest = match.group(3)

            cd_suffix = ''
            has_c = False
            if rest:
                cd_match = re.match(r'-CD(\d+)$', rest, flags=re.IGNORECASE)
                if cd_match:
                    cd_suffix = f'-CD{cd_match.group(1)}'
                    rest = rest[:-len(cd_suffix)]
                c_match = re.match(r'[-_]?(ch|C)$', rest, flags=re.IGNORECASE)
                ab_match = re.match(r'[-_]?(A|B)$', rest, flags=re.IGNORECASE)
                if c_match:
                    has_c = True
                elif ab_match:
                    letter = ab_match.group(1).upper()
                    cd_suffix = f'-CD{1 if letter == "A" else 2}'

            code = f"{prefix}-{num}"
            if has_c and not code.endswith('-C'):
                code += '-C'
            code += cd_suffix

            return code, True

        match = re.match(r'^([A-Z]+)(\d+)(.*)', s_upper)
        if match:
            prefix = match.group(1)
            num = match.group(2)
            rest = match.group(3)

            cd_suffix = ''
            has_c = False
            if rest:
                cd_match = re.match(r'-CD(\d+)$', rest, flags=re.IGNORECASE)
                if cd_match:
                    cd_suffix = f'-CD{cd_match.group(1)}'
                    rest = rest[:-len(cd_suffix)]
                c_match = re.match(r'[-_]?(ch|C)$', rest, flags=re.IGNORECASE)
                ab_match = re.match(r'[-_]?(A|B)$', rest, flags=re.IGNORECASE)
                if c_match:
                    has_c = True
                elif ab_match:
                    letter = ab_match.group(1).upper()
                    cd_suffix = f'-CD{1 if letter == "A" else 2}'

            code = f"{prefix}-{num}"
            if has_c and not code.endswith('-C'):
                code += '-C'
            code += cd_suffix

            return code, True

        match = re.match(r'^(\d{3})([A-Z]+)(\d+)(.*)', s_upper)
        if match:
            num_prefix = match.group(1)
            prefix = match.group(2)
            num = match.group(3)
            rest = match.group(4)

            cd_suffix = ''
            has_c = False
            if rest:
                cd_match = re.match(r'-CD(\d+)$', rest, flags=re.IGNORECASE)
                if cd_match:
                    cd_suffix = f'-CD{cd_match.group(1)}'
                    rest = rest[:-len(cd_suffix)]
                c_match = re.match(r'[-_]?(ch|C)$', rest, flags=re.IGNORECASE)
                ab_match = re.match(r'[-_]?(A|B)$', rest, flags=re.IGNORECASE)
                if c_match:
                    has_c = True
                elif ab_match:
                    letter = ab_match.group(1).upper()
                    cd_suffix = f'-CD{1 if letter == "A" else 2}'

            code = f"{num_prefix}{prefix}-{num}"
            if has_c and not code.endswith('-C'):
                code += '-C'
            code += cd_suffix

            return code, True

        return None, False

    def _extract_from_parentheses(self, s):
        match = re.search(r'\(([A-Za-z]+-\d+)\)', s)
        if match:
            return match.group(1).upper()
        match = re.search(r'（([A-Za-z]+-\d+)）', s)
        if match:
            return match.group(1).upper()
        return None

    def _process_xvt_pattern(self, s):
        match = re.search(r'([A-Z]{2,4})-(\d+)', s)
        if match:
            return f"{match.group(1)}-{match.group(2)}", True
        return None, False

    def _process_mgmr_pattern(self, s):
        match = re.match(r'(\d{3})(MGMR)-(\d+)', s, re.IGNORECASE)
        if match:
            return f"{match.group(2).upper()}-{match.group(3)}", True
        return None, False

    def _process_arso_pattern(self, s):
        match = re.match(r'ARSO-?(\d+)', s, re.IGNORECASE)
        if match:
            num = match.group(1)
            if len(num) >= 5:
                return f"ARSO-{num}", True
        match = re.search(r'ARSO(\d+)', s, re.IGNORECASE)
        if match:
            num = match.group(1)
            if len(num) >= 5:
                return f"ARSO-{num}", True
        return None, False

    def _process_dv_pattern(self, s):
        match = re.match(r'DV-?(\d+)(.*)', s, re.IGNORECASE)
        if match:
            num = match.group(1)
            rest = match.group(2)
            if rest:
                rest_clean = re.sub(r'[-_]?(A|B|C)$', '', rest, flags=re.IGNORECASE)
                if rest_clean != rest:
                    rest = rest_clean
            return f"DV-{num}", True
        return None, False

    def _light_cleanup(self, s):
        s = re.sub(r'\s*-\s*', '-', s)
        s = re.sub(r'[-_]+', '-', s)
        s = re.sub(r'-+', '-', s)
        s = re.sub(r'-{2,}', '-', s)
        s = re.sub(r'\.$', '', s)
        s = s.strip('-')
        return s

    def _final_cleanup(self, s):
        s = re.sub(r'[-_]+', '-', s)
        s = re.sub(r'-+', '-', s)
        s = re.sub(r'-{2,}', '-', s)
        s = re.sub(r'\.$', '', s)
        s = re.sub(r'\s+', '', s)
        s = re.sub(r'\d{4}-\d{2}-\d{2}$', '', s)
        s = re.sub(r'\d{6}$', '', s)
        s = s.strip('-')
        return s

    def _should_skip_normalization(self, name: str) -> bool:
        skip_keywords = ['G-Area', 'GAREA', 'pgm', 'S-Cute', 'Mywife', 'Maxi-247', 'gachinco', 'pacopacomama', 'OnlyFans', 'BrazzersExxtra']
        name_upper = name.upper()
        for kw in skip_keywords:
            if kw.upper() in name_upper:
                return True
        return False

    def extract_normalized_id(self, raw_name: str) -> str:
        original = raw_name.strip()

        if self._should_skip_normalization(original):
            return original

        fc2_result, fc2_found = self._process_fc2(original)
        if fc2_found:
            result = fc2_result
        else:
            heyzo_result, heyzo_found = self._process_heyzo(original)
            if heyzo_found:
                result = heyzo_result
            else:
                cwp_result, cwp_found = self._process_cwp(original)
                if cwp_found:
                    result = cwp_result
                else:
                    carib_result, carib_found = self._process_carib(original)
                    if carib_found:
                        result = carib_result
                    else:
                        divx_result, divx_found = self._process_divx_nike(original)
                        if divx_found:
                            result = divx_result
                        else:
                            paren_result = self._extract_from_parentheses(original)
                            if paren_result:
                                working = paren_result
                                working = self._clean_non_ascii(working)
                                working = self._remove_video_extensions(working)
                                working = self._remove_resolution_tags(working)
                                working = self._light_cleanup(working)
                                code, found = self._general_extract(working)
                                if found:
                                    result = self._final_cleanup(code)
                                else:
                                    if working:
                                        result = self._final_cleanup(working)
                                    else:
                                        result = raw_name
                            else:
                                working = original

                                working = re.sub(r'\[[^\]]*\.(?:com|tv|me|la|xyz|cc|net|org|pro)[^\]]*\]', '', working, flags=re.IGNORECASE)
                                working = re.sub(r'\[(?:JAV|Uncensored)\]', '', working, flags=re.IGNORECASE)
                                working = re.sub(r'\(([^)]+)\)', r'\1', working)
                                working = re.sub(r'\[([^\]]+)\]', r'\1', working)
                                working = re.sub(r'【([^】]+)】', r'\1', working)

                                working = self._remove_video_extensions(working)

                                working = self._preprocess_disc_suffixes(working)

                                working = self._remove_ad_text(working)

                                working = self._remove_resolution_tags(working)

                                working = self._remove_xyz_domain(working)

                                working = self._clean_non_ascii(working)

                                working = self._remove_date_patterns(working)

                                working = self._remove_site_names(working)

                                working = re.sub(r'\s+', ' ', working).strip()

                                working = self._light_cleanup(working)

                                code, found = self._extract_code_with_prefix_check(working, original.upper())
                                if found:
                                    result = self._final_cleanup(code)
                                else:
                                    code, found = self._general_extract(working)
                                    if found:
                                        result = self._final_cleanup(code)
                                    else:
                                        code, found = self._process_arso_pattern(working)
                                        if found:
                                            result = self._final_cleanup(code)
                                        else:
                                            code, found = self._process_dv_pattern(working)
                                            if found:
                                                result = self._final_cleanup(code)
                                            else:
                                                xvt_result, xvt_found = self._process_xvt_pattern(working)
                                                if xvt_found:
                                                    result = xvt_result
                                                else:
                                                    mgmr_result, mgmr_found = self._process_mgmr_pattern(working)
                                                    if mgmr_found:
                                                        result = mgmr_result
                                                    else:
                                                        result = raw_name

        if '中文' in original and not result.endswith('-C'):
            result += '-C'

        return result

    def batch_process(self, file_list):
        return [(f, self.extract_normalized_id(f)) for f in file_list]