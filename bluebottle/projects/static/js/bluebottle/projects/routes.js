/**
 *  Router Map
 */

App.Router.map(function(){
    this.resource('projectList', {path: '/projects'}, function() {
        this.route('search');
    });

    this.resource('project', {path: '/projects/:project_id'}, function() {
        this.resource('projectPlan', {path: '/plan'});
        this.resource('projectTasks', {path: '/tasks'}, function(){
            this.resource('projectTask', {path: '/:task_id'}, function(){});
            this.resource('projectTaskNew', {path: '/new'});
            this.resource('projectTaskEdit', {path: '/:task_id/edit'});
        });
    });

    this.resource('myProjectList', {path: '/my/projects'});

    this.resource('myProject', {path: '/my/projects/:id'}, function() {
        this.route('basics');
        this.route('description');
        this.route('details');
        this.route('location');
        this.route('media');

        this.route('organisation');
        this.route('legal');
        this.route('ambassadors');

        this.route('bank');
        this.route('campaign');
        this.route('budget');

        this.route('submit');
    });

    this.resource('partner', {path: '/pp/:partner_organization_id'});

});


/**
 * Project Routes
 */

App.ProjectRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        // Crap hack because Ember somehow doesn't strip query-params.
        // FIXME: Find out this -should- work.
        var project_id = params.project_id.split('?')[0];
        var page =  App.Project.find(project_id);
        var route = this;
        page.on('becameError', function() {
            route.transitionTo('projectList');
        });
        return page;
    }

});


App.ProjectIndexRoute = Em.Route.extend({
    // This way the ArrayController won't hold an immutable array thus it can be extended with more wallposts.
    setupController: function(controller, model) {
        // Only reload wall-posts if switched to another project.
        var parent_id = this.modelFor('project').get('id');
        if (controller.get('parent_id') != parent_id){
            controller.set('page', 1);
            controller.set('parent_id', parent_id);

            // Load wall-posts for this project
            var store = this.get('store');
            store.find('wallPost', {'parent_type': 'project', 'parent_id': parent_id}).then(function(items){
                controller.set('meta', items.get('meta'));
                controller.set('model', items.toArray());
            });
        }
    }
});


/**
 * My Projects
 * - Manage your project(s)
 */

App.MyProjectListRoute = Em.Route.extend(App.ScrollToTop, {
    model: function(params) {
        return App.MyProject.find();
    },
    setupController: function(controller, model) {
        this._super(controller, model);
    }

});


App.MyProjectRoute = Em.Route.extend({
    // Load the Project
    model: function(params) {
        var store = this.get('store');
        if (params.id == 'new' || params.id == 'null') {
            return App.MyProject.createRecord();
        }
        return store.find('myProject', params.id);
    }
});

App.MyProjectIndexRoute = Em.Route.extend({
    redirect: function(){
        this.transitionTo('myProject.basics');
    }

});


App.MyProjectSubRoute = Em.Route.extend({
    redirect: function() {
        var phase = this.modelFor('myProject').get('phase');
        switch(phase) {
            case 'plan-submitted':
                this.transitionTo('myProjectReview');
                break;
            case 'plan-rejected':
                this.transitionTo('myProjectRejected');
                break;
        }
    },

    model: function(params) {
        return this.modelFor('myProject');
    },

    exit: function() {
        if (this.get('controller')) {
            this.get('controller').stopEditing();
        }
    }
});

App.MyProjectBasicsRoute = App.MyProjectSubRoute.extend({});
App.MyProjectDescriptionRoute = App.MyProjectSubRoute.extend({});
App.MyProjectLocationRoute = App.MyProjectSubRoute.extend({});
App.MyProjectMediaRoute = App.MyProjectSubRoute.extend({});
App.MyProjectSubmitRoute = App.MyProjectSubRoute.extend({});

App.MyProjectCampaignRoute = App.MyProjectSubRoute.extend({});


App.MyProjectDetailsRoute = App.MyProjectSubRoute.extend({

    setupController: function(controller, model) {
        this._super(controller, model);
        controller.set('fields', App.ProjectDetailField.find());
    }
});


App.MyProjectBudgetRoute = App.MyProjectSubRoute.extend({
    setupController: function(controller, model){
        this._super(controller, model);

        var numBudgetLines = model.get('budgetLines').get('content').length;
        if(numBudgetLines === 0){
            Em.run.next(function(){
                controller.send('addBudgetLine');
            });
        } else {
            // there are budget lines, and it's not the initial click -> show errors
            controller.set('showBudgetError', true);
        }
    }
});

App.MyProjectOrganisationRoute = App.MyProjectSubRoute.extend({

    setupController: function(controller, model) {
        this._super(controller, model);
        var transaction = this.get('store').transaction();
        transaction.add(model);
        controller.set('organizations', App.MyOrganization.find());
        var organization =  model.get('organization');
        if (Ember.isNone(organization)) {
            var organization = App.MyOrganization.createRecord();
            model.set('organization', organization);
        }
        transaction.add(organization);
    }
});

App.MyProjectBankRoute = App.MyProjectSubRoute.extend({});

App.MyProjectLegalRoute = App.MyProjectSubRoute.extend({});
