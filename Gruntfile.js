module.exports = function(grunt) {
	grunt.initConfig({
		pkg: grunt.file.readJSON('package.json'),

		concat: {
			dist: {
				src: ['static/js/dev/*.js'],
				dest: 'static/js/production.js'
			}
		},
		uglify: {
			build: {
				src: 'static/js/production.js',
				dest: 'static/production.min.js'
			}
		},
		concat_css: {
			all: {
				src: ['static/css/dev/*.css'],
				dest: 'static/production.css'
			}
		},
		watch: {
			scripts: {
				files: ['static/js/dev/*.js'],
				tasks: ['concat', 'uglify'],
				options: {
					spawn: false
				}
			},
			css : {
				files: ['static/css/dev/*.css'],
				tasks: ['concat_css'],
				options: {
					spawn: false
				}
			}
		}
	});

	grunt.loadNpmTasks('grunt-contrib-concat');
	grunt.loadNpmTasks('grunt-contrib-uglify');
	grunt.loadNpmTasks('grunt-concat-css');
	grunt.loadNpmTasks('grunt-contrib-watch');

	grunt.registerTask('default', ['concat', 'uglify', 'concat_css', 'watch']);
}